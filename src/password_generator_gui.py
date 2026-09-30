# ================= IMPORTS =================
import tkinter as tk
from tkinter import messagebox, ttk
import uuid
import hashlib
import os
import json
import base64
import secrets
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken

# ================= CONFIG =================

APP_NAME = "xLocker"

LICENSE_PUBLIC_KEY = b"""-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEL0BxgAvkhmnpQ55bLgV8gPOT4Ptu
1cdvUYamqWZMJCD5uP4q8FYbAkuN53wCM4asBUxWDc17KmaY0mTXXL8yAg==
-----END PUBLIC KEY-----"""

MIN_MASTER_PASSWORD_LENGTH = 14
SCRYPT_COST = 2**15
SCRYPT_BLOCK_SIZE = 8
SCRYPT_PARALLELISM = 1
LEGACY_PBKDF2_ITERATIONS = 200000

# ================= DIRETÓRIO SEGURO =================

APPDATA_DIR = os.path.join(
    os.getenv("LOCALAPPDATA"),
    APP_NAME
)

os.makedirs(APPDATA_DIR, exist_ok=True)

LICENCA_ARQUIVO = os.path.join(APPDATA_DIR, "licenca.json")
AUTH_ARQUIVO = os.path.join(APPDATA_DIR, "auth.json")
VAULT_ARQUIVO = os.path.join(APPDATA_DIR, "vault.dat")

# ===== TEMA MODERNO =====
BG = "#0e1117"
SIDEBAR = "#161b22"
CARD = "#1f2630"
GREEN = "#00ff88"
BTN_GREEN = "#00aa55"
WHITE = "#ffffff"
GRAY = "#9da5b4"

AUTOLOCK_TIME = 120000  # 2 minutos

# ================= ROOT =================

root = tk.Tk()
root.title(APP_NAME)
root.geometry("1200x720")
root.configure(bg=BG)

chave_sessao = None
dashboard_tree = None
status_label = None
busca_var = tk.StringVar()
categoria_var = tk.StringVar()

autolock_job = None
clipboard_clear_job = None
clipboard_password = None

# ================= LICENÇA =================

def gerar_machine_id():
    return hashlib.sha256(str(uuid.getnode()).encode()).hexdigest().upper()

def payload_licenca(machine_id, cliente):
    return json.dumps(
        {"cliente": cliente, "machine_id": machine_id},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True
    ).encode("utf-8")

def validar_licenca(machine_id, cliente, chave):
    if not all(isinstance(valor, str) for valor in (machine_id, cliente, chave)):
        return False
    try:
        assinatura = base64.b64decode(
            chave.encode("ascii"),
            altchars=b"-_",
            validate=True
        )
        public_key = serialization.load_pem_public_key(LICENSE_PUBLIC_KEY)
        public_key.verify(
            assinatura,
            payload_licenca(machine_id, cliente),
            ec.ECDSA(hashes.SHA256())
        )
        return True
    except (InvalidSignature, ValueError, TypeError, UnicodeEncodeError):
        return False

def salvar_licenca(cliente, chave):
    with open(LICENCA_ARQUIVO, "w") as f:
        json.dump({"cliente": cliente, "chave": chave}, f)

def carregar_licenca():
    if not os.path.exists(LICENCA_ARQUIVO):
        return None
    with open(LICENCA_ARQUIVO, "r") as f:
        return json.load(f)

# ================= CRIPTO =================

def derivar_chave(senha, salt, auth=None):
    if auth and auth.get("kdf") == "scrypt":
        kdf = Scrypt(
            salt=salt,
            length=32,
            n=SCRYPT_COST,
            r=SCRYPT_BLOCK_SIZE,
            p=SCRYPT_PARALLELISM
        )
    else:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=LEGACY_PBKDF2_ITERATIONS,
        )
    return base64.urlsafe_b64encode(kdf.derive(senha.encode("utf-8")))

def salvar_credenciais_mestra(senha, dados):
    salt = os.urandom(16)
    chave = derivar_chave(senha, salt, {"kdf": "scrypt"})
    fernet = Fernet(chave)
    auth = {
        "salt": base64.b64encode(salt).decode("ascii"),
        "kdf": "scrypt"
    }
    arquivo_auth_tmp = AUTH_ARQUIVO + ".tmp"
    arquivo_vault_tmp = VAULT_ARQUIVO + ".tmp"

    arquivos_anteriores = {}
    for caminho in (AUTH_ARQUIVO, VAULT_ARQUIVO):
        if os.path.exists(caminho):
            with open(caminho, "rb") as arquivo:
                arquivos_anteriores[caminho] = arquivo.read()
        else:
            arquivos_anteriores[caminho] = None

    try:
        with open(arquivo_auth_tmp, "w", encoding="utf-8") as arquivo:
            json.dump(auth, arquivo)
        with open(arquivo_vault_tmp, "wb") as arquivo:
            arquivo.write(fernet.encrypt(json.dumps(dados).encode("utf-8")))

        os.replace(arquivo_vault_tmp, VAULT_ARQUIVO)
        os.replace(arquivo_auth_tmp, AUTH_ARQUIVO)
    except OSError:
        for caminho, conteudo in arquivos_anteriores.items():
            if conteudo is None:
                if os.path.exists(caminho):
                    os.remove(caminho)
            else:
                caminho_tmp = caminho + ".rollback"
                with open(caminho_tmp, "wb") as arquivo:
                    arquivo.write(conteudo)
                os.replace(caminho_tmp, caminho)
        raise
    finally:
        for caminho in (arquivo_auth_tmp, arquivo_vault_tmp):
            if os.path.exists(caminho):
                os.remove(caminho)

    return chave

def criar_senha_mestra():
    senha = prompt_modal("Crie sua senha mestra:", True)
    if not senha:
        return False
    if len(senha) < MIN_MASTER_PASSWORD_LENGTH:
        messagebox.showerror(
            "Senha fraca",
            f"Use uma senha mestra com pelo menos {MIN_MASTER_PASSWORD_LENGTH} caracteres."
        )
        return False
    confirmacao = prompt_modal("Confirme sua senha mestra:", True)
    if senha != confirmacao:
        messagebox.showerror("Erro", "As senhas não coincidem.")
        return False

    chave = salvar_credenciais_mestra(senha, {})
    global chave_sessao
    chave_sessao = chave
    return True

def autenticar_senha():
    if not os.path.exists(AUTH_ARQUIVO):
        return criar_senha_mestra()

    senha = prompt_modal("Digite sua senha mestra:", True)
    if not senha:
        return False

    with open(AUTH_ARQUIVO, "r", encoding="utf-8") as f:
        auth = json.load(f)

    salt = base64.b64decode(auth["salt"])
    chave = derivar_chave(senha, salt, auth)

    try:
        fernet = Fernet(chave)
        with open(VAULT_ARQUIVO, "rb") as arquivo:
            dados = json.loads(fernet.decrypt(arquivo.read()).decode("utf-8"))
    except InvalidToken:
        messagebox.showerror("Erro", "Senha incorreta.")
        return False

    if auth.get("kdf") != "scrypt" or len(senha) < MIN_MASTER_PASSWORD_LENGTH:
        nova_senha = prompt_modal(
            f"Atualize sua senha mestra (mínimo de {MIN_MASTER_PASSWORD_LENGTH} caracteres):",
            True
        )
        if not nova_senha:
            return False
        if len(nova_senha) < MIN_MASTER_PASSWORD_LENGTH:
            messagebox.showerror(
                "Senha fraca",
                f"Use pelo menos {MIN_MASTER_PASSWORD_LENGTH} caracteres."
            )
            return False
        confirmacao = prompt_modal("Confirme sua nova senha mestra:", True)
        if nova_senha != confirmacao:
            messagebox.showerror("Erro", "As senhas não coincidem.")
            return False
        chave = salvar_credenciais_mestra(nova_senha, dados)

    global chave_sessao
    chave_sessao = chave
    return True
# ================= MODAL =================

def prompt_modal(texto, senha=False):
    modal = tk.Toplevel(root)
    modal.configure(bg=BG)
    modal.grab_set()
    modal.geometry("350x160")
    modal.resizable(False, False)

    tk.Label(modal, text=texto, bg=BG, fg=WHITE).pack(pady=10)

    entry = tk.Entry(
        modal,
        show="*" if senha else "",
        bg="#222",
        fg=GREEN,
        insertbackground=GREEN
    )
    entry.pack(pady=5)

    resultado = {"valor": None}

    def confirmar():
        resultado["valor"] = entry.get()
        modal.destroy()

    tk.Button(modal, text="OK",
              bg=BTN_GREEN,
              command=confirmar).pack(pady=10)

    modal.wait_window()
    return resultado["valor"]

# ================= VAULT =================

def carregar_vault():
    fernet = Fernet(chave_sessao)
    dados = fernet.decrypt(open(VAULT_ARQUIVO, "rb").read())
    return json.loads(dados.decode())

def salvar_vault(dados):
    fernet = Fernet(chave_sessao)
    with open(VAULT_ARQUIVO, "wb") as f:
        f.write(fernet.encrypt(json.dumps(dados).encode()))

def gerar_senha_forte():
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%&*"
    return ''.join(secrets.choice(chars) for _ in range(16))

# ================= CRUD =================

def criar_conta():
    nome = prompt_modal("Nome da conta:")
    categoria = prompt_modal("Categoria:")
    if not nome:
        return
    dados = carregar_vault()
    dados[nome] = {
        "senha": gerar_senha_forte(),
        "categoria": categoria or "Geral"
    }
    salvar_vault(dados)
    atualizar_lista()

def editar_conta():
    item = dashboard_tree.selection()
    if not item:
        return
    nome = dashboard_tree.item(item)["values"][0]
    dados = carregar_vault()
    nova = prompt_modal("Nova senha:")
    if nova:
        dados[nome]["senha"] = nova
        salvar_vault(dados)
        atualizar_lista()

def excluir_conta():
    item = dashboard_tree.selection()
    if not item:
        return
    nome = dashboard_tree.item(item)["values"][0]
    dados = carregar_vault()
    del dados[nome]
    salvar_vault(dados)
    atualizar_lista()

def visualizar_ou_copiar(event):
    item = dashboard_tree.identify_row(event.y)
    coluna = dashboard_tree.identify_column(event.x)
    if not item or coluna != "#3":
        return

    nome = dashboard_tree.item(item)["values"][0]
    dados = carregar_vault()
    senha = dados[nome]["senha"]

    x, _, largura, _ = dashboard_tree.bbox(item, column=coluna)
    clique_relativo = event.x - x

    if clique_relativo < largura / 2:
        dashboard_tree.item(item, values=(nome,
                                          dados[nome]["categoria"],
                                          senha))
        root.after(3000, lambda:
                   dashboard_tree.item(item,
                                       values=(nome,
                                               dados[nome]["categoria"],
                                               "👁  📋")))
    else:
        global clipboard_clear_job, clipboard_password
        if clipboard_clear_job:
            root.after_cancel(clipboard_clear_job)
        root.clipboard_clear()
        root.clipboard_append(senha)
        clipboard_password = senha
        clipboard_clear_job = root.after(
            30000,
            lambda: limpar_clipboard(senha)
        )
        messagebox.showinfo("Copiado", "Senha copiada!")

def limpar_clipboard(senha=None):
    global clipboard_clear_job, clipboard_password
    if senha is not None and clipboard_password != senha:
        return
    if clipboard_clear_job:
        root.after_cancel(clipboard_clear_job)
    clipboard_clear_job = None
    try:
        if clipboard_password and root.clipboard_get() == clipboard_password:
            root.clipboard_clear()
    except tk.TclError:
        pass
    clipboard_password = None

# ================= BUSCA + FILTRO =================

def atualizar_lista():
    dashboard_tree.delete(*dashboard_tree.get_children())
    dados = carregar_vault()

    termo = busca_var.get().lower()
    filtro_categoria = categoria_var.get()

    categorias = set()

    for nome, info in dados.items():
        categorias.add(info["categoria"])

        if termo and termo not in nome.lower():
            continue
        if filtro_categoria and filtro_categoria != "Todas":
            if info["categoria"] != filtro_categoria:
                continue

        dashboard_tree.insert("", "end",
                              values=(nome,
                                      info["categoria"],
                                      "👁  📋"))

    categoria_combo["values"] = ["Todas"] + sorted(list(categorias))

# ================= AUTO LOCK =================

def resetar_timer(event=None):
    global autolock_job
    if autolock_job:
        root.after_cancel(autolock_job)
    autolock_job = root.after(AUTOLOCK_TIME, bloquear)

def bloquear():
    limpar_clipboard()
    messagebox.showinfo("Sessão", "Bloqueado por inatividade.")
    root.destroy()

def fechar_aplicacao():
    limpar_clipboard()
    root.destroy()

# ================= UI =================

def construir_interface():
    global dashboard_tree, categoria_combo, status_label
    root.protocol("WM_DELETE_WINDOW", fechar_aplicacao)

    root.bind_all("<Any-KeyPress>", resetar_timer)
    root.bind_all("<Any-Button>", resetar_timer)

    # SIDEBAR
    sidebar = tk.Frame(root, bg=SIDEBAR, width=250)
    sidebar.pack(side="left", fill="y")

    tk.Label(sidebar,
             text=APP_NAME,
             fg=GREEN,
             bg=SIDEBAR,
             font=("Segoe UI", 20, "bold")).pack(pady=30)

    # MAIN
    main = tk.Frame(root, bg=BG)
    main.pack(fill="both", expand=True)

    topbar = tk.Frame(main, bg=BG)
    topbar.pack(fill="x", pady=10)

    tk.Entry(topbar,
             textvariable=busca_var,
             bg=CARD,
             fg=WHITE,
             insertbackground=WHITE,
             width=40).pack(side="left", padx=10)

    busca_var.trace_add("write", lambda *args: atualizar_lista())

    categoria_combo = ttk.Combobox(topbar,
                                   textvariable=categoria_var,
                                   state="readonly",
                                   width=15)
    categoria_combo.pack(side="left")
    categoria_combo.bind("<<ComboboxSelected>>",
                         lambda e: atualizar_lista())
    categoria_var.set("Todas")

    # BOTÕES
    btn_frame = tk.Frame(main, bg=BG)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Criar",
              bg=BTN_GREEN,
              command=criar_conta).pack(side="left", padx=5)

    tk.Button(btn_frame, text="Editar",
              bg=BTN_GREEN,
              command=editar_conta).pack(side="left", padx=5)

    tk.Button(btn_frame, text="Excluir",
              bg=BTN_GREEN,
              command=excluir_conta).pack(side="left", padx=5)

    # TABELA
    style = ttk.Style()
    style.theme_use("default")
    style.configure("Treeview",
                    background=CARD,
                    foreground=WHITE,
                    fieldbackground=CARD,
                    rowheight=35)

    dashboard_tree = ttk.Treeview(
        main,
        columns=("Conta", "Categoria", "Ação"),
        show="headings"
    )

    dashboard_tree.heading("Conta", text="Conta")
    dashboard_tree.heading("Categoria", text="Categoria")
    dashboard_tree.heading("Ação", text="")

    dashboard_tree.column("Ação", width=120, anchor="center")

    dashboard_tree.pack(fill="both", expand=True, padx=40, pady=20)
    dashboard_tree.bind("<Button-1>", visualizar_ou_copiar)

    # STATUS BAR
    status = tk.Frame(root, bg=SIDEBAR, height=25)
    status.pack(side="bottom", fill="x")

    cliente = carregar_licenca()["cliente"]

    status_label = tk.Label(status,
                            text=f"{cliente} | Licença válida | © Lienz",
                            bg=SIDEBAR,
                            fg=GRAY)
    status_label.pack(side="left", padx=10)

    atualizar_lista()
    resetar_timer()

# ================= FLUXO =================

def iniciar():
    licenca = carregar_licenca()

    if not licenca:
        abrir_ativacao()
        return

    if validar_licenca(gerar_machine_id(), licenca["cliente"], licenca["chave"]):
        if autenticar_senha():
            construir_interface()
    else:
        abrir_ativacao()

def abrir_ativacao():
    modal = tk.Toplevel(root)
    modal.grab_set()

    machine_id = gerar_machine_id()

    tk.Label(modal, text="Machine ID").pack()
    e = tk.Entry(modal, width=60)
    e.insert(0, machine_id)
    e.config(state="readonly")
    e.pack()

    tk.Label(modal, text="Nome do Cliente").pack()
    entry_cliente = tk.Entry(modal)
    entry_cliente.pack()

    tk.Label(modal, text="Chave de Ativação").pack()
    entry_chave = tk.Entry(modal, width=60)
    entry_chave.pack()

    def ativar():
        cliente = entry_cliente.get().strip()
        chave = entry_chave.get().strip()

        if validar_licenca(machine_id, cliente, chave):
            salvar_licenca(cliente, chave)
            modal.destroy()
            iniciar()
        else:
            messagebox.showerror("Erro", "Licença inválida.")

    tk.Button(modal, text="Ativar",
              command=ativar).pack(pady=10)

# ================= START =================

iniciar()
root.mainloop()
