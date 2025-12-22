# app.py
# ISP Consulte Tools — Streamlit (pt-BR)
#
# Importa planilhas .xlsx e cadastra:
#  - Assuntos (su_oss_assunto)
#  - Diagnósticos (su_diagnostico)
#
# v10:
# - Adiciona download das planilhas modelo (Assuntos / Diagnósticos) dentro do app
# - Templates ficam em ./templates e aparecem em Home + nas páginas de criação
#
# Rodar:
#   pip install -r requirements.txt
#   streamlit run app.py

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import os
import base64
import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv
from textwrap import dedent


# ============================
# i18n
# ============================

I18N = {'en': {'app_name': 'ISP Consulte Tools',
        'apply_session': '💾 Apply (session)',
        'auth_401': '401: invalid credential or cookie required.',
        'auth_ok': 'Auth OK (not 401).',
        'auth_unknown': 'Could not confirm. See JSON above.',
        'backoff': 'Backoff (sec)',
        'btn_apply_bulk': '⚡ Apply to selected',
        'btn_clear_cache': '🧹 Clear page cache',
        'btn_clear_selection': '🧹 Clear selection',
        'btn_fetch_subjects': '🔄 Fetch subjects',
        'btn_save_put': '💾 Save changes (PUT)',
        'btn_select_all_filtered': '✅ Select all (current filter)',
        'chk_save_only_changed': 'Save only changed items',
        'chk_save_only_selected': 'Save only selected (if any)',
        'chk_validate_before_save': 'Validate required fields before saving',
        'clear_overrides': '🧹 Clear overrides',
        'cookie_label': 'Cookie (IXC_COOKIE) — optional',
        'create_diagnostics': 'Create Diagnostics',
        'create_subjects': 'Create Subjects',
        'created': 'Created/validated',
        'download_csv': '⬇️ Download CSV report',
        'download_edit_csv': '⬇️ Download edit report (CSV)',
        'download_edit_json': '⬇️ Download compact_edit_subjects (JSON)',
        'download_json': '⬇️ Download compact_jsoncolumns (JSON)',
        'download_template_diagnostics': '⬇️ Download template — Diagnostics',
        'download_template_subjects': '⬇️ Download template — Subjects',
        'downloads': 'Downloads',
        'errors': 'Errors',
        'go_create_diagnostics': '➡️ Go to Create Diagnostics',
        'go_create_subjects': '➡️ Go to Create Subjects',
        'hint_bulk': 'Tip: mark **select** column and use bulk edit to change a field for all selected.',
        'home': 'Home',
        'host_label': 'IXC Host (IXC_BASE_URL)',
        'label_bulk_field': 'Field (bulk edit)',
        'label_bulk_value': 'Value',
        'label_columns': 'Fields to show/edit',
        'label_filter': 'Filter (subject/description)',
        'label_max_pages': 'Max pages (safety)',
        'label_max_total': 'Total limit (0 = all)',
        'label_rp': 'Rows per page (rp)',
        'label_selected': 'Selected',
        'language': 'Language',
        'manage_subjects': 'Manage Subjects',
        'manage_subjects_help': 'Fetch, edit and save (PUT) subjects one by one.',
        'masked_summary': 'Masked summary',
        'max_retries': 'Max retries',
        'missing_config': 'Missing Host and/or Token (use Settings or .env).',
        'msg_bulk_applied': "Applied '{field}={value}' to {n} items.",
        'msg_finished': 'Done. OK: {ok} | Errors: {err}',
        'msg_loaded_n': 'Loaded {n} subjects.',
        'msg_missing_id': "Column 'id' is not visible. Include 'id' to save.",
        'msg_no_data_manage': 'Click **Fetch subjects** to load data.',
        'msg_no_selection': 'No selected rows.',
        'msg_nothing_to_save': 'No changes detected to save.',
        'need_column': 'Spreadsheet must include required column: ',
        'need_file': 'Upload the spreadsheet to start.',
        'page_create_diagnostics_title': 'Create Diagnostics',
        'page_create_subjects_title': 'Create Subjects',
        'page_home_title': 'Home',
        'page_manage_subjects_title': 'Manage Subjects',
        'page_settings_title': 'Settings',
        'present_config': 'Host and token present (masked).',
        'preview_sheet': 'Spreadsheet preview (first rows)',
        'project_info': 'Project info',
        'put_saving': 'Saving',
        'result': 'Result',
        'run_create': '🚀 Create in IXC',
        'run_validate': '✅ Validate only',
        'session_only_note': 'Settings below are **session-only** (not saved to disk or browser).',
        'settings': 'Settings',
        'status_config': 'Auth/config status (quick)',
        'summary': 'Summary',
        'support': 'Support',
        'tab_auth': 'Authentication',
        'tab_personalization': 'Personalization',
        'template_missing': 'Template not found in project: ',
        'templates': 'Templates',
        'test_auth': '🔎 Test authentication (HEAD)',
        'theme': 'Theme',
        'theme_auto': 'Auto (system)',
        'theme_dark': 'Dark',
        'theme_light': 'Light',
        'timeout': 'Timeout (sec)',
        'token_label': 'Basic token (IXC_AUTH_BASIC) — not saved',
        'upload_xlsx': 'Upload spreadsheet (.xlsx)',
        'what_can_do': 'What you can do',
        'restore_env': '🧹 Restore from .env',
        'applied_session_ok': 'Settings applied for this session.',
        'restored_env_ok': 'Settings restored from .env.'},
 'pt-BR': {'app_name': 'ISP Consulte Tools',
           'apply_session': '💾 Aplicar (sessão)',
           'auth_401': '401: credencial inválida ou cookie exigido. Se seu cURL usa IXC_Session, preencha o Cookie.',
           'auth_ok': 'Autenticação OK (não retornou 401).',
           'auth_unknown': 'Não deu para confirmar. Veja o JSON acima.',
           'backoff': 'Backoff (seg)',
           'btn_apply_bulk': '⚡ Aplicar em selecionados',
           'btn_clear_cache': '🧹 Limpar cache desta tela',
           'btn_clear_selection': '🧹 Limpar seleção',
           'btn_fetch_subjects': '🔄 Buscar assuntos',
           'btn_save_put': '💾 Salvar alterações (PUT)',
           'btn_select_all_filtered': '✅ Selecionar todos (filtro atual)',
           'chk_save_only_changed': 'Salvar somente itens alterados',
           'chk_save_only_selected': 'Salvar somente selecionados (se houver)',
           'chk_validate_before_save': 'Validar obrigatórios antes de salvar',
           'clear_overrides': '🧹 Limpar overrides',
           'cookie_label': 'Cookie (IXC_COOKIE) — opcional',
           'create_diagnostics': 'Criar Diagnósticos',
           'create_subjects': 'Criar Assuntos',
           'created': 'Criados/validados',
           'download_csv': '⬇️ Baixar relatório CSV',
           'download_edit_csv': '⬇️ Baixar relatório de edição (CSV)',
           'download_edit_json': '⬇️ Baixar compact_edicao_assuntos (JSON)',
           'download_json': '⬇️ Baixar compact_jsoncolumns (JSON)',
           'download_template_diagnostics': '⬇️ Baixar modelo — Diagnósticos',
           'download_template_subjects': '⬇️ Baixar modelo — Assuntos',
           'downloads': 'Downloads',
           'errors': 'Erros',
           'go_create_diagnostics': '➡️ Ir para Criar Diagnósticos',
           'go_create_subjects': '➡️ Ir para Criar Assuntos',
           'hint_bulk': 'Dica: marque a coluna **selecionar** e use a edição em massa para alterar um campo em todos '
                        'selecionados.',
           'home': 'Home',
           'host_label': 'Host do IXC (IXC_BASE_URL)',
           'label_bulk_field': 'Campo (edição em massa)',
           'label_bulk_value': 'Valor',
           'label_columns': 'Campos para exibir/editar',
           'label_filter': 'Filtro (assunto/descrição)',
           'label_max_pages': 'Máx. páginas (segurança)',
           'label_max_total': 'Limite total (0 = todos)',
           'label_rp': 'Registros por página (rp)',
           'label_selected': 'Selecionados',
           'language': 'Idioma',
           'manage_subjects': 'Gerenciar Assuntos',
           'manage_subjects_help': 'Busque, edite e salve (PUT) os assuntos item a item.',
           'masked_summary': 'Resumo (mascarado)',
           'max_retries': 'Max retries',
           'missing_config': 'Falta configurar Host e/ou Token (use Configurações ou .env).',
           'msg_bulk_applied': "Aplicado '{field}={value}' em {n} itens.",
           'msg_finished': 'Finalizado. OK: {ok} | Erros: {err}',
           'msg_loaded_n': 'Carregados {n} assuntos.',
           'msg_missing_id': "Coluna 'id' não está visível. Inclua 'id' nos campos para salvar.",
           'msg_no_data_manage': 'Clique em **Buscar assuntos** para carregar os dados.',
           'msg_no_selection': 'Nenhuma linha selecionada.',
           'msg_nothing_to_save': 'Nenhuma alteração detectada para salvar.',
           'need_column': 'A planilha precisa ter a coluna obrigatória: ',
           'need_file': 'Envie a planilha para começar.',
           'page_create_diagnostics_title': 'Criar Diagnósticos',
           'page_create_subjects_title': 'Criar Assuntos',
           'page_home_title': 'Home',
           'page_manage_subjects_title': 'Gerenciar Assuntos',
           'page_settings_title': 'Configurações',
           'present_config': 'Host e token presentes (credenciais mascaradas).',
           'preview_sheet': 'Preview da planilha (primeiras linhas)',
           'project_info': 'Informações do projeto',
           'put_saving': 'Salvando',
           'result': 'Resultado',
           'run_create': '🚀 Criar no IXC',
           'run_validate': '✅ Apenas validar',
           'session_only_note': 'As configurações abaixo podem ser aplicadas **somente na sessão atual** (não salva em '
                                'disco nem no navegador).',
           'settings': 'Configurações',
           'status_config': 'Status de autenticação/config (rápido)',
           'summary': 'Resumo',
           'support': 'Suporte',
           'tab_auth': 'Autenticação',
           'tab_personalization': 'Personalização',
           'template_missing': 'Template não encontrado no projeto: ',
           'templates': 'Planilhas modelo',
           'test_auth': '🔎 Testar autenticação (HEAD)',
           'theme': 'Tema',
           'theme_auto': 'Automático (sistema)',
           'theme_dark': 'Escuro',
           'theme_light': 'Claro',
           'timeout': 'Timeout (seg)',
           'token_label': 'Token Basic (IXC_AUTH_BASIC) — não é salvo',
           'upload_xlsx': 'Upload da planilha (.xlsx)',
           'what_can_do': 'O que é possível fazer',
           'restore_env': '🧹 Restaurar do .env',
           'applied_session_ok': 'Configurações aplicadas nesta sessão.',
           'restored_env_ok': 'Configurações restauradas do .env.'}}


def tr(key: str) -> str:
    lang = st.session_state.get("lang", "pt-BR")
    return I18N.get(lang, I18N["pt-BR"]).get(key, key)


# ============================
# Streamlit config + session defaults
# ============================

st.set_page_config(page_title="ISP Consulte Tools", layout="wide", initial_sidebar_state="expanded")

if "lang" not in st.session_state:
    st.session_state.lang = "pt-BR"

# theme_mode: auto | dark | light
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "auto"

if "page_key" not in st.session_state:
    st.session_state.page_key = "home"  # home | subjects | diagnostics | settings


def set_page(key: str) -> None:
    st.session_state.page_key = key
    st.rerun()


# ============================
# THEME (Auto by system via CSS prefers-color-scheme)
# ============================

BASE_THEME_CSS = r"""
<style>
:root{
  --bg: #f6f7ff;
  --text: #15162b;
  --muted: rgba(21,22,43,0.72);
  --panel: rgba(20,20,40,0.03);
  --panel2: rgba(20,20,40,0.06);
  --border: rgba(20,20,40,0.10);
  --border2: rgba(20,20,40,0.18);
  --sidebar-bg: #f5f6ff;
}
@media (prefers-color-scheme: dark){
  :root{
    --bg: radial-gradient(circle at top left, #1a1b3a 0%, #0b0b16 60%, #070710 100%);
    --text: #e9e9ff;
    --muted: rgba(233,233,255,0.72);
    --panel: rgba(255,255,255,0.03);
    --panel2: rgba(255,255,255,0.06);
    --border: rgba(255,255,255,0.08);
    --border2: rgba(255,255,255,0.18);
    --sidebar-bg: radial-gradient(circle at top left, #1a1b3a 0%, #0b0b16 60%, #070710 100%);
  }
}
[data-testid="stAppViewContainer"]{ background: var(--bg) !important; color: var(--text) !important; }
[data-testid="stHeader"]{ background: transparent !important; }
[data-testid="stToolbar"]{ right: 1rem; }
html, body, [data-testid="stAppViewContainer"] * { color: var(--text); }
p, li { color: var(--muted); }
section[data-testid="stSidebar"]{ background: var(--sidebar-bg) !important; }
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
  height: 80vh;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  padding-top: 0.35rem;
  padding-bottom: 0.35rem;
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE/Edge */
}
section[data-testid="stSidebar"] [data-testid="stSidebarContent"]::-webkit-scrollbar{ width:0; height:0; display:none; }
section[data-testid="stSidebar"] div.stVerticalBlock { display:flex; flex-direction:column; min-height: 100vh; }
.sidebar-title { text-align:center; font-weight:800; font-size:20px; margin-top:0.10rem; margin-bottom:0.25rem; }
section[data-testid="stSidebar"] .stButton>button{
  border-radius: 12px !important;
  border: 1px solid var(--border) !important;
  background: var(--panel) !important;
  padding: 0.50rem 0.72rem !important;
  text-align: left !important;
  justify-content: flex-start !important;
}
section[data-testid="stSidebar"] .stButton>button:hover{
  border-color: var(--border2) !important;
  background: var(--panel2) !important;
}
div[data-testid="stTabs"] button[role="tab"]{ border-radius: 10px 10px 0 0 !important; }
section[data-testid="stSidebar"] hr { margin: 0.35rem 0 !important; }
section[data-testid="stSidebar"] .stButton { margin-bottom: 0.32rem !important; }

/* ISP: sidebar menu button left align */
section[data-testid="stSidebar"] .stButton > button{
  width:100% !important;
  display:flex !important;
  justify-content:flex-start !important;
  align-items:center !important;
  text-align:left !important;
  padding-left:14px !important;
  gap: .35rem !important;
}
/* alguns temas do Streamlit centralizam via wrapper interno */
section[data-testid="stSidebar"] .stButton > button > div,
section[data-testid="stSidebar"] .stButton > button > span,
section[data-testid="stSidebar"] .stButton > button > div > div{
  width:100% !important;
  display:flex !important;
  justify-content:flex-start !important;
  align-items:center !important;
}
/* container de markdown dentro do botão */
section[data-testid="stSidebar"] .stButton > button [data-testid="stMarkdownContainer"],
section[data-testid="stSidebar"] .stButton > button [data-testid="stMarkdownContainer"] p,
section[data-testid="stSidebar"] .stButton > button p,
section[data-testid="stSidebar"] .stButton > button span{
  width:100% !important;
  text-align:left !important;
  margin:0 !important;
}
/* remove possíveis margens automáticas que empurram o texto pro centro */
section[data-testid="stSidebar"] .stButton > button [data-testid="stMarkdownContainer"] p{
  margin-left:0 !important;
  margin-right:auto !important;
}

/* ISP: remove scroll do menu lateral (mantém tudo visível) */
section[data-testid="stSidebar"] [data-testid="stSidebarContent"]{
  overflow-y: hidden !important;
}
</style>
"""

OVERRIDE_DARK = r"""
<style>
:root{
  --bg: radial-gradient(circle at top left, #1a1b3a 0%, #0b0b16 60%, #070710 100%) !important;
  --text: #e9e9ff !important;
  --muted: rgba(233,233,255,0.72) !important;
  --panel: rgba(255,255,255,0.03) !important;
  --panel2: rgba(255,255,255,0.06) !important;
  --border: rgba(255,255,255,0.08) !important;
  --border2: rgba(255,255,255,0.18) !important;
  --sidebar-bg: radial-gradient(circle at top left, #1a1b3a 0%, #0b0b16 60%, #070710 100%) !important;
}
section[data-testid="stSidebar"] hr { margin: 0.35rem 0 !important; }
section[data-testid="stSidebar"] .stButton { margin-bottom: 0.32rem !important; }
</style>
"""

OVERRIDE_LIGHT = r"""
<style>
:root{
  --bg: #f6f7ff !important;
  --text: #15162b !important;
  --muted: rgba(21,22,43,0.72) !important;
  --panel: rgba(20,20,40,0.03) !important;
  --panel2: rgba(20,20,40,0.06) !important;
  --border: rgba(20,20,40,0.10) !important;
  --border2: rgba(20,20,40,0.18) !important;
  --sidebar-bg: #f5f6ff !important;
}
section[data-testid="stSidebar"] hr { margin: 0.35rem 0 !important; }
section[data-testid="stSidebar"] .stButton { margin-bottom: 0.32rem !important; }
</style>
"""

st.markdown(BASE_THEME_CSS, unsafe_allow_html=True)
if st.session_state.theme_mode == "dark":
    st.markdown(OVERRIDE_DARK, unsafe_allow_html=True)
elif st.session_state.theme_mode == "light":
    st.markdown(OVERRIDE_LIGHT, unsafe_allow_html=True)


# ============================
# Templates helpers
# ============================

APP_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = APP_DIR / "templates"


def read_template_bytes(filename: str) -> Optional[bytes]:
    path = TEMPLATES_DIR / filename
    if not path.exists():
        return None
    return path.read_bytes()


def templates_block() -> None:
    st.subheader(tr("templates"))
    col1, col2 = st.columns(2)

    b1 = read_template_bytes("modelo_assuntos.xlsx")
    with col1:
        if b1 is None:
            st.warning(tr("template_missing") + "modelo_assuntos.xlsx")
        else:
            st.download_button(
                tr("download_template_subjects"),
                data=b1,
                file_name="modelo_assuntos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

    b2 = read_template_bytes("modelo_diagnosticos.xlsx")
    with col2:
        if b2 is None:
            st.warning(tr("template_missing") + "modelo_diagnosticos.xlsx")
        else:
            st.download_button(
                tr("download_template_diagnostics"),
                data=b2,
                file_name="modelo_diagnosticos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )


# ============================
# .env + runtime config
# ============================

load_dotenv()

ENV_IXC_BASE_URL = (os.getenv("IXC_BASE_URL", "") or "").strip().rstrip("/")
ENV_IXC_AUTH_BASIC = (os.getenv("IXC_AUTH_BASIC", "") or "").strip()
ENV_IXC_COOKIE = (os.getenv("IXC_COOKIE", "") or "").strip()
ENV_IXC_TIMEOUT_SECONDS = float(os.getenv("IXC_TIMEOUT_SECONDS", "30"))
ENV_IXC_MAX_RETRIES = int(os.getenv("IXC_MAX_RETRIES", "3"))
ENV_IXC_RETRY_BACKOFF_SECONDS = float(os.getenv("IXC_RETRY_BACKOFF_SECONDS", "1.5"))

ENDPOINT_ASSUNTO = "/webservice/v1/su_oss_assunto"
ENDPOINT_DIAGNOSTICO = "/webservice/v1/su_diagnostico"


def _sanitize(v: str) -> str:
    v = (v or "").strip()
    for _ in range(3):
        v = v.strip().strip('"').strip("'").strip()
    return v

def normalize_auth_to_header(auth_input: str) -> str:
    """Aceita:
    - token cru: '17:xxxx...'
    - base64 puro
    - 'Basic <base64>'
    Retorna sempre 'Basic <base64>' (para header Authorization).
    """
    v = _sanitize(auth_input or "")
    if not v:
        return ""
    if v.lower().startswith("basic "):
        v = v[6:].strip()

    # Converte automaticamente token cru (id:token) para base64
    if ":" in v and " " not in v:
        try:
            v = base64.b64encode(v.encode("utf-8")).decode("ascii")
        except Exception:
            pass

    return f"Basic {v}"


def mask_middle(s: str, keep_left: int = 10, keep_right: int = 6) -> str:
    s = s or ""
    if len(s) <= keep_left + keep_right + 3:
        return "*" * len(s)
    return s[:keep_left] + "..." + s[-keep_right:]


def get_runtime_config() -> Dict[str, Any]:
    base_url = st.session_state.get("cfg_base_url") or ENV_IXC_BASE_URL
    auth = st.session_state.get("cfg_auth_basic") or ENV_IXC_AUTH_BASIC
    cookie = st.session_state.get("cfg_cookie") or ENV_IXC_COOKIE
    return {
        "base_url": (base_url or "").strip().rstrip("/"),
        "auth_basic": (auth or "").strip(),
        "cookie": (cookie or "").strip(),
        "timeout_seconds": float(st.session_state.get("cfg_timeout_seconds") or ENV_IXC_TIMEOUT_SECONDS),
        "max_retries": int(st.session_state.get("cfg_max_retries") or ENV_IXC_MAX_RETRIES),
        "retry_backoff_seconds": float(st.session_state.get("cfg_retry_backoff_seconds") or ENV_IXC_RETRY_BACKOFF_SECONDS),
    }


def build_headers(cfg: Dict[str, Any]) -> Dict[str, str]:
    auth_header = normalize_auth_to_header(cfg.get("auth_basic", ""))
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if auth_header:
        headers["Authorization"] = auth_header

    cookie = cfg.get("cookie", "")
    if cookie:
        headers["Cookie"] = cookie

    return headers


# ============================
# API client
# ============================

@dataclass
class IXCResponse:
    ok: bool
    http_status: Optional[int]
    data: Optional[dict]
    text: str


def test_auth(cfg: Dict[str, Any], session: Optional[requests.Session] = None) -> Dict[str, Any]:
    """Faz um HEAD no endpoint do IXC (sem body) para validar se o Authorization está ok."""
    url = f"{cfg['base_url']}{ENDPOINT_ASSUNTO}"
    headers = build_headers(cfg)
    s = session or requests.Session()
    s = session or requests.Session()
    try:
        resp = s.request("HEAD", url, headers=headers, timeout=cfg["timeout_seconds"])
        return {
            "ok": resp.status_code != 401,
            "status_code": resp.status_code,
            "response_headers": dict(resp.headers),
            "response_text": (resp.text or "")[:500],
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def post_to_endpoint(cfg: Dict[str, Any], endpoint_path: str, payload: Dict[str, str], session: Optional[requests.Session] = None) -> IXCResponse:
    url = f"{cfg['base_url']}{endpoint_path}"
    headers = build_headers(cfg)
    s = session or requests.Session()

    last_text = ""
    last_data: Optional[dict] = None
    last_status: Optional[int] = None

    for attempt in range(1, cfg["max_retries"] + 1):
        try:
            resp = s.post(
                url,
                headers=headers,
                data=json.dumps(payload, ensure_ascii=False),
                timeout=cfg["timeout_seconds"],
            )
            last_status = resp.status_code
            last_text = resp.text or ""
            try:
                last_data = resp.json()
            except Exception:
                last_data = None

            if 200 <= resp.status_code < 300:
                return IXCResponse(ok=True, http_status=resp.status_code, data=last_data, text=last_text)

            if resp.status_code in (429, 500, 502, 503, 504):
                time.sleep(cfg["retry_backoff_seconds"] * attempt)
                continue

            return IXCResponse(ok=False, http_status=resp.status_code, data=last_data, text=last_text)

        except requests.RequestException as e:
            last_text = str(e)
            last_status = None
            last_data = None
            time.sleep(cfg["retry_backoff_seconds"] * attempt)

    return IXCResponse(ok=False, http_status=last_status, data=last_data, text=last_text)


def put_to_endpoint(cfg: Dict[str, Any], endpoint_path: str, payload: Dict[str, str], session: Optional[requests.Session] = None) -> IXCResponse:
    url = f"{cfg['base_url']}{endpoint_path}"
    headers = build_headers(cfg)
    s = session or requests.Session()

    last_text = ""
    last_data: Optional[dict] = None
    last_status: Optional[int] = None

    for attempt in range(1, cfg["max_retries"] + 1):
        try:
            resp = s.put(
                url,
                headers=headers,
                data=json.dumps(payload, ensure_ascii=False),
                timeout=cfg["timeout_seconds"],
            )
            last_text = (resp.text or "")[:5000]
            last_status = resp.status_code
            try:
                last_data = resp.json()
            except Exception:
                last_data = None

            if 200 <= resp.status_code < 300:
                return IXCResponse(ok=True, http_status=resp.status_code, data=last_data, text=last_text)

            if resp.status_code in (429, 500, 502, 503, 504):
                time.sleep(cfg["retry_backoff_seconds"] * attempt)
                continue

            return IXCResponse(ok=False, http_status=resp.status_code, data=last_data, text=last_text)

        except requests.RequestException as e:
            last_text = str(e)
            last_status = None
            time.sleep(cfg["retry_backoff_seconds"] * attempt)

    return IXCResponse(ok=False, http_status=last_status, data=last_data, text=last_text)


def parse_ixc_list_response(data: Any) -> Optional[List[dict]]:
    if isinstance(data, dict) and isinstance(data.get("registros"), list):
        return data["registros"]
    if isinstance(data, dict) and isinstance(data.get("rows"), list):
        out: List[dict] = []
        for r in data["rows"]:
            if isinstance(r, dict) and isinstance(r.get("cell"), dict):
                out.append(r["cell"])
            elif isinstance(r, dict):
                out.append(r)
        return out
    if isinstance(data, dict) and isinstance(data.get("data"), list):
        return data["data"]
    return None


def ensure_id(records: List[dict]) -> List[dict]:
    out: List[dict] = []
    for r in records:
        rr = dict(r or {})
        if "id" not in rr:
            for k in list(rr.keys()):
                if str(k).endswith(".id"):
                    rr["id"] = rr.get(k)
                    break
        out.append(rr)
    return out


def listar_assuntos_todos(cfg: Dict[str, Any], rp: int = 1000, max_pages: int = 50, max_total: int = 0, session: Optional[requests.Session] = None) -> Tuple[List[dict], List[dict]]:
    """
    Lista assuntos com GET + header ixcsoft:listar e JSON no body (como no cURL).
    - rp: registros por página (>=1)
    - max_pages: limite de páginas para segurança
    - max_total: limite total de registros (0 = todos)
    Retorna (records, debug_pages).
    """
    url = f"{cfg['base_url']}{ENDPOINT_ASSUNTO}"
    headers = build_headers(cfg)
    headers = dict(headers)
    headers["ixcsoft"] = "listar"

    s = session or requests.Session()
    _own_session = session is None

    rp = max(1, int(rp))
    max_pages = max(1, int(max_pages))
    max_total = max(0, int(max_total))

    all_records: List[dict] = []
    debug_pages: List[dict] = []

    for page in range(1, max_pages + 1):
        payload = {
            "qtype": "su_oss_assunto.id",
            "query": "1",
            "oper": ">=",
            "page": str(page),
            "rp": str(rp),
            "sortname": "su_oss_assunto.id",
            "sortorder": "asc",
        }

        last_text = ""
        last_data: Optional[dict] = None
        last_status: Optional[int] = None
        ok = False

        for attempt in range(1, cfg["max_retries"] + 1):
            try:
                resp = s.request(
                    "GET",
                    url,
                    headers=headers,
                    data=json.dumps(payload, ensure_ascii=False),
                    timeout=cfg["timeout_seconds"],
                )
                last_text = (resp.text or "")[:5000]
                last_status = resp.status_code
                try:
                    last_data = resp.json()
                except Exception:
                    last_data = None

                if 200 <= resp.status_code < 300:
                    ok = True
                    break

                if resp.status_code in (429, 500, 502, 503, 504):
                    time.sleep(cfg["retry_backoff_seconds"] * attempt)
                    continue

                break
            except requests.RequestException as e:
                last_text = str(e)
                last_status = None
                time.sleep(cfg["retry_backoff_seconds"] * attempt)

        debug_pages.append({"page": page, "http_status": last_status, "json": last_data, "text": last_text[:2000]})

        if not ok:
            break

        records = parse_ixc_list_response(last_data or {})
        if not records:
            break

        all_records.extend(records)

        if max_total and len(all_records) >= max_total:
            all_records = all_records[:max_total]
            break

        if len(records) < rp:
            break

    if _own_session:
        s.close()

    return ensure_id(all_records), debug_pages


# ============================
# Payload normalization/validation
# ============================

REQUIRED_ASSUNTO = [
    "assunto",
    "ativo",
    "layout_impressao",
    "numero_de_vias",
    "exige_comodato_finalizar_os",
    "exige_produto_finalizar_os",
    "tipo_comissao",
    "considerar_sla",
    "metas_horas_abertura_ticket",
]

COND_ASSUNTO = [
    ("exige_comodato_finalizar_os", "quantidade_equipamentos"),
    ("exige_produto_finalizar_os", "quantidade_produtos"),
]

REQUIRED_DIAGNOSTICO = ["descricao", "ativo"]


def _is_empty(v: Any) -> bool:
    return v is None or (isinstance(v, str) and v.strip() == "")


def normalize_value(v: Any) -> str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    if isinstance(v, (pd.Timestamp,)):
        if pd.isna(v):
            return ""
        return v.isoformat()
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if v.is_integer():
            return str(int(v))
        return str(v)
    s = str(v)
    if s.strip().lower() == "nan":
        return ""
    return s.strip()



def parse_bool_value(v: Any) -> bool:
    """Converte valores variados (bool/str/int) para bool (checkbox do Streamlit)."""
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    try:
        if isinstance(v, float) and pd.isna(v):
            return False
    except Exception:
        pass
    s = str(v).strip().lower()
    if s in ("1", "true", "t", "yes", "y", "s", "sim", "on"):
        return True
    return False


def row_to_payload(row: pd.Series) -> Dict[str, str]:
    return {str(k).strip(): normalize_value(v) for k, v in row.items()}


def validate_required(payload: Dict[str, str], required: List[str]) -> List[str]:
    errors: List[str] = []
    for f in required:
        if f not in payload or _is_empty(payload.get(f)):
            errors.append(f"Campo obrigatório ausente/vazio: {f}")
    return errors


def validate_assunto(payload: Dict[str, str]) -> List[str]:
    errors = validate_required(payload, REQUIRED_ASSUNTO)
    for flag_field, qty_field in COND_ASSUNTO:
        flag_val = (payload.get(flag_field) or "").strip().upper()
        if flag_val == "S":
            qty_val = (payload.get(qty_field) or "").strip()
            if qty_val in ("", "0", "0.0"):
                errors.append(f"Campo '{qty_field}' é obrigatório quando '{flag_field}' = 'S'")
    return errors


def validate_diagnostico(payload: Dict[str, str]) -> List[str]:
    return validate_required(payload, REQUIRED_DIAGNOSTICO)


# ============================
# Sidebar (buttons — same tab)
# ============================

with st.sidebar:
    logo_path = Path(__file__).parent / "assets" / "logo-isp-consulte.png"
    if logo_path.exists():
        st.image(str(logo_path), use_container_width=True)
    else:
        st.markdown("<div class='sidebar-title'>ISP Consulte</div>", unsafe_allow_html=True)
    st.markdown("<hr style='opacity:.25; margin:10px 0 14px 0;'>", unsafe_allow_html=True)


if st.sidebar.button("🏠 " + tr("home"), use_container_width=True):
    set_page("home")

if st.sidebar.button("🧾 " + tr("create_subjects"), use_container_width=True):
    set_page("subjects")

if st.sidebar.button("📝 " + tr("manage_subjects"), use_container_width=True):
    set_page("manage_subjects")

if st.sidebar.button("🩺 " + tr("create_diagnostics"), use_container_width=True):
    set_page("diagnostics")
st.sidebar.markdown("---")
if st.sidebar.button("⚙️ " + tr("settings"), use_container_width=True):
    set_page("settings")


cfg = get_runtime_config()


# ============================
# Shared import UI
# ============================

def import_page(
    *,
    page_title: str,
    endpoint_path: str,
    name_col: str,
    validate_fn,
    skip_label: str,
    report_prefix: str,
) -> None:
    st.title(page_title)
    st.caption("Envie o .xlsx, valide e crie no IXC com progresso e relatório de erros.")

    with st.expander(tr("templates"), expanded=False):
        templates_block()

    with st.expander(tr("status_config"), expanded=False):
        if not cfg["base_url"] or not cfg["auth_basic"]:
            st.error(tr("missing_config"))
        else:
            st.success(tr("present_config"))
            st.write(f"- Host: `{cfg['base_url']}`")
            st.write(f"- Cookie informado: `{bool(_sanitize(cfg.get('cookie') or ''))}`")
            st.write(f"- Endpoint: `{cfg['base_url']}{endpoint_path}`")

    uploaded = st.file_uploader(tr("upload_xlsx"), type=["xlsx"], key=f"uploader_{report_prefix}")

    colA, colB, colC, colD = st.columns([1, 1, 1, 1])
    with colA:
        dry_run = st.checkbox("Somente validar (dry run)", value=False, key=f"dry_{report_prefix}")
    with colB:
        stop_on_error = st.checkbox("Parar no primeiro erro", value=False, key=f"stop_{report_prefix}")
    with colC:
        skip_empty = st.checkbox(skip_label, value=True, key=f"skip_{report_prefix}")
    with colD:
        show_payload_preview = st.checkbox("Mostrar preview do payload", value=False, key=f"preview_{report_prefix}")

    if uploaded is None:
        st.info(tr("need_file"))
        return

    try:
        df = pd.read_excel(uploaded)
    except Exception as e:
        st.error(f"Não consegui ler o arquivo .xlsx: {e}")
        return

    if df.empty:
        st.warning("A planilha está vazia.")
        return

    df.columns = [str(c).strip() for c in df.columns]
    if name_col not in df.columns:
        st.error(tr("need_column") + f"'{name_col}'")
        return

    df_work = df.copy()
    if skip_empty:
        df_work = df_work[~df_work[name_col].isna()]
        df_work = df_work[df_work[name_col].astype(str).str.strip() != ""]

    total = len(df_work)

    st.subheader(tr("summary"))
    st.write(f"**Total para criar:** {total}")
    st.write(f"**Total de colunas (campos):** {len(df_work.columns)}")

    with st.expander(tr("preview_sheet")):
        st.dataframe(df_work.head(50), use_container_width=True)

    run = st.button(tr("run_validate") if dry_run else tr("run_create"), type="primary", key=f"run_{report_prefix}")
    if not run:
        return

    if not dry_run and (not cfg["base_url"] or not cfg["auth_basic"]):
        st.error("Configure Host e Token antes de criar.")
        return

    progress = st.progress(0)
    status = st.empty()

    results: List[Dict[str, Any]] = []
    responses_compact: List[Dict[str, Any]] = []
    created = 0
    errors = 0

    for i, (idx, row) in enumerate(df_work.iterrows(), start=1):
        payload = row_to_payload(row)
        item_name = payload.get(name_col, f"(linha {idx})")
        validation_errors = validate_fn(payload)

        if show_payload_preview:
            with st.expander(f"Payload (linha {idx}) — {item_name}"):
                st.json(payload)

        result_row: Dict[str, Any] = {
            "linha_excel": int(idx) + 2,
            name_col: item_name,
            "status": "",
            "http_status": "",
            "mensagem": "",
        }

        if validation_errors:
            errors += 1
            msg = " | ".join(validation_errors)
            result_row.update({"status": "ERRO_VALIDACAO", "mensagem": msg})
            results.append(result_row)
            responses_compact.append({
                name_col: item_name,
                "linha_excel": result_row["linha_excel"],
                "ok": False,
                "tipo": "validacao",
                "erros": validation_errors,
                "payload": payload,
            })

            if stop_on_error:
                status.error(f"Erro de validação na linha {result_row['linha_excel']}: {item_name}")
                break

            status.warning(f"[{i}/{total}] Validação falhou: {item_name}")
            progress.progress(int(i / max(total, 1) * 100))
            continue

        if dry_run:
            created += 1
            result_row.update({"status": "OK_VALIDADO", "mensagem": "Payload válido (dry run)."})
            results.append(result_row)
            responses_compact.append({
                name_col: item_name,
                "linha_excel": result_row["linha_excel"],
                "ok": True,
                "tipo": "dry_run",
                "payload": payload,
            })
            status.info(f"[{i}/{total}] Validado: {item_name}")
            progress.progress(int(i / max(total, 1) * 100))
            continue

        status.info(f"[{i}/{total}] Criando: {item_name}")
        resp = post_to_endpoint(cfg, endpoint_path, payload)

        responses_compact.append({
            name_col: item_name,
            "linha_excel": result_row["linha_excel"],
            "ok": resp.ok,
            "http_status": resp.http_status,
            "response_json": resp.data,
            "response_text": resp.text[:5000],
            "payload": payload,
        })

        if resp.ok:
            created += 1
            msg = ""
            if isinstance(resp.data, dict):
                msg = str(resp.data.get("message") or resp.data.get("msg") or "")
            result_row.update({"status": "CRIADO", "http_status": resp.http_status, "mensagem": msg})
            results.append(result_row)
        else:
            errors += 1
            msg = ""
            if isinstance(resp.data, dict):
                msg = str(resp.data.get("message") or resp.data.get("msg") or resp.data)
            else:
                msg = resp.text
            result_row.update({"status": "ERRO_API", "http_status": resp.http_status, "mensagem": msg})
            results.append(result_row)

            if stop_on_error:
                status.error(f"Erro na API ao criar '{item_name}'.")
                break

        progress.progress(int(i / max(total, 1) * 100))

    st.divider()
    st.subheader(tr("result"))
    st.write(f"✅ {tr('created')}: **{created}**")
    st.write(f"❌ {tr('errors')}: **{errors}**")

    result_df = pd.DataFrame(results)
    st.dataframe(result_df, use_container_width=True, height=420)

    st.subheader(tr("downloads"))
    result_csv = result_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        tr("download_csv"),
        data=result_csv,
        file_name=f"relatorio_import_{report_prefix}.csv",
        mime="text/csv",
        key=f"dlcsv_{report_prefix}",
    )

    compact_json = json.dumps(responses_compact, ensure_ascii=False, indent=2).encode("utf-8")
    st.download_button(
        tr("download_json"),
        data=compact_json,
        file_name=f"compact_{report_prefix}.json",
        mime="application/json",
        key=f"dlj_{report_prefix}",
    )


# ============================
# Pages
# ============================

def page_home() -> None:
    st.title(tr("page_home_title"))

    st.subheader(tr("project_info"))
    st.write(
        """
Este sistema importa planilhas **.xlsx** e cadastra itens no IXC via API.

- **Criar Assuntos** → endpoint `su_oss_assunto`
- **Criar Diagnósticos** → endpoint `su_diagnostico`

Cada **coluna** = um campo do JSON do endpoint  
Cada **linha** = um item a cadastrar
        """.strip()
    )

    st.subheader(tr("what_can_do"))
    st.write(
        """
- Upload de planilha
- Validação de campos obrigatórios (e condicionais no caso de Assuntos)
- Criação com progresso
- Download do relatório e do JSON compacto (payload + retorno da API)
        """.strip()
    )

    templates_block()

    st.subheader(tr("support"))
    st.info("Coloque aqui seus contatos (WhatsApp/e-mail) quando quiser.")

    if cfg["base_url"]:
        st.code(
            "\n".join(
                [
                    f"Assuntos: {cfg['base_url']}{ENDPOINT_ASSUNTO}",
                    f"Diagnósticos: {cfg['base_url']}{ENDPOINT_DIAGNOSTICO}",
                ]
            )
        )
    else:
        st.warning("Host ainda não configurado (use Configurações).")

    


def page_settings() -> None:
    st.title(tr("page_settings_title"))
    st.caption(tr("session_only_note"))

    cfg = get_runtime_config()

    tab_auth, tab_pers = st.tabs([f"🔐 {tr('tab_auth')}", f"🎨 {tr('tab_personalization')}"])

    with tab_auth:

        # Form para aplicar configurações somente quando o usuário clicar em "Aplicar (sessão)"
        with st.form("form_settings_auth", clear_on_submit=False):
            col1, col2 = st.columns([2, 2])

            with col1:
                base_url = st.text_input(
                    tr("host_label"),
                    value=cfg["base_url"],
                    key="form_cfg_base_url",
                    placeholder="https://ixc.seudominio.com.br",
                )
                auth_basic = st.text_input(
                    tr("token_label"),
                    value=cfg["auth_basic"],
                    key="form_cfg_auth_basic",
                    type="password",
                    placeholder="17:xxxx... ou Basic abcdef... (ou só o base64)",
                )
                st.caption("Dica: cole o token no formato 17:xxxx (id:token). O sistema converte para Base64 automaticamente.")
                cookie = st.text_input(
                    tr("cookie_label"),
                    value=cfg["cookie"],
                    key="form_cfg_cookie",
                    placeholder="IXC_Session=... (se necessário)",
                )

            with col2:
                timeout_seconds = st.number_input(
                    tr("timeout"),
                    min_value=5.0,
                    max_value=120.0,
                    value=float(cfg["timeout_seconds"]),
                    step=1.0,
                    key="form_cfg_timeout_seconds",
                )
                max_retries = st.number_input(
                    tr("max_retries"),
                    min_value=0,
                    max_value=10,
                    value=int(cfg["max_retries"]),
                    step=1,
                    key="form_cfg_max_retries",
                )
                retry_backoff_seconds = st.number_input(
                    tr("backoff"),
                    min_value=0.0,
                    max_value=10.0,
                    value=float(cfg["retry_backoff_seconds"]),
                    step=0.5,
                    key="form_cfg_retry_backoff_seconds",
                )

            st.markdown("---")
            c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
            with c1:
                rp = st.number_input(
                    tr("label_rp"),
                    min_value=1,
                    max_value=5000,
                    value=int(st.session_state.get("mg_rp", 1000)),
                    step=1,
                    key="form_mg_rp",
                )
            with c2:
                max_pages = st.number_input(
                    tr("label_max_pages"),
                    min_value=1,
                    max_value=50,
                    value=int(st.session_state.get("mg_max_pages", 50)),
                    step=1,
                    key="form_mg_max_pages",
                )
            with c3:
                max_total = st.number_input(
                    tr("label_max_total"),
                    min_value=0,
                    max_value=1000000,
                    value=int(st.session_state.get("mg_max_total", 0)),
                    step=1,
                    key="form_mg_max_total",
                )
            with c4:
                st.write("**Endpoint:**")
                preview_base = (base_url or "").strip().rstrip("/")
                st.code(f"{preview_base}{ENDPOINT_ASSUNTO}")

            st.markdown("---")
            b1, b2 = st.columns([2, 2])
            with b1:
                apply_clicked = st.form_submit_button(tr("apply_session"), use_container_width=True)
            with b2:
                restore_clicked = st.form_submit_button(tr("restore_env"), use_container_width=True)

        # Ações pós-submit (fora do form)
        if restore_clicked:
            st.session_state["cfg_base_url"] = (ENV_IXC_BASE_URL or "").strip().rstrip("/")
            st.session_state["cfg_auth_basic"] = (ENV_IXC_AUTH_BASIC or "").strip()
            st.session_state["cfg_cookie"] = (ENV_IXC_COOKIE or "").strip()
            st.session_state["cfg_timeout_seconds"] = float(ENV_IXC_TIMEOUT_SECONDS)
            st.session_state["cfg_max_retries"] = int(ENV_IXC_MAX_RETRIES)
            st.session_state["cfg_retry_backoff_seconds"] = float(ENV_IXC_RETRY_BACKOFF_SECONDS)
            st.session_state["mg_rp"] = 1000
            st.session_state["mg_max_pages"] = 50
            st.session_state["mg_max_total"] = 0
            st.success(tr("restored_env_ok"))
            st.rerun()

        if apply_clicked:
            st.session_state["cfg_base_url"] = (base_url or "").strip().rstrip("/")
            st.session_state["cfg_auth_basic"] = (auth_basic or "").strip()
            st.session_state["cfg_cookie"] = (cookie or "").strip()
            st.session_state["cfg_timeout_seconds"] = float(timeout_seconds)
            st.session_state["cfg_max_retries"] = int(max_retries)
            st.session_state["cfg_retry_backoff_seconds"] = float(retry_backoff_seconds)
            st.session_state["mg_rp"] = int(rp)
            st.session_state["mg_max_pages"] = int(max_pages)
            st.session_state["mg_max_total"] = int(max_total)
            st.success(tr("applied_session_ok"))
            st.rerun()

        st.markdown("---")
        if st.button(tr("test_auth")):
            r = test_auth(get_runtime_config())
            st.json(r)
            if r.get("status_code") == 401:
                st.error(tr("auth_401"))
            elif r.get("ok"):
                st.success(tr("auth_ok"))
            else:
                st.warning(tr("auth_unknown"))

    with tab_pers:
        colA, colB = st.columns([2, 2])

        with colA:
            lang = st.selectbox(tr("language"), ["pt-BR", "en"], index=0 if st.session_state.lang == "pt-BR" else 1)

        with colB:
            theme_labels = {
                "auto": tr("theme_auto"),
                "dark": tr("theme_dark"),
                "light": tr("theme_light"),
            }
            theme_options = ["auto", "dark", "light"]
            theme = st.selectbox(
                tr("theme"),
                theme_options,
                format_func=lambda x: theme_labels.get(x, x),
                index=theme_options.index(st.session_state.theme_mode if st.session_state.theme_mode in theme_options else "auto"),
                help="Por padrão, segue o modo do seu dispositivo.",
            )

        changed = False
        if lang != st.session_state.lang:
            st.session_state.lang = lang
            changed = True
        if theme != st.session_state.theme_mode:
            st.session_state.theme_mode = theme
            changed = True

        if changed:
            st.rerun()


def page_subjects() -> None:
    import_page(
        page_title=tr("page_create_subjects_title"),
        endpoint_path=ENDPOINT_ASSUNTO,
        name_col="assunto",
        validate_fn=validate_assunto,
        skip_label="Pular linhas com 'assunto' vazio",
        report_prefix="assuntos",
    )


def page_manage_subjects() -> None:
    cfg = get_runtime_config()

    st.title(tr("page_manage_subjects_title"))
    st.caption(tr("manage_subjects_help"))

    if not cfg["base_url"] or not cfg["auth_basic"]:
        st.error(tr("missing_config"))
        return

    # ----------------------------
    # Configuração / Filtros
    # ----------------------------
    with st.expander("⚙️ Configurações e filtros", expanded=True):
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            rp = st.number_input(
                tr("label_rp"),
                min_value=1,
                max_value=5000,
                value=int(st.session_state.get("mg_rp", 1000)),
                step=1,
            )
        with c2:
            # por segurança, limita em 50 páginas (pode ajustar depois)
            max_pages = st.number_input(
                tr("label_max_pages"),
                min_value=1,
                max_value=50,
                value=int(st.session_state.get("mg_max_pages", 50)),
                step=1,
            )
        with c3:
            max_total = st.number_input(
                tr("label_max_total"),
                min_value=0,
                max_value=200000,
                value=int(st.session_state.get("mg_max_total", 0)),
                step=1,
                help="0 = buscar todos (respeitando o limite de páginas).",
            )

        st.session_state["mg_rp"] = int(rp)
        st.session_state["mg_max_pages"] = int(max_pages)
        st.session_state["mg_max_total"] = int(max_total)

        st.write("**Endpoint:**")
        st.code(f"{cfg['base_url']}{ENDPOINT_ASSUNTO}")

        b1, b2 = st.columns([1, 1])
        with b1:
            fetch = st.button(tr("btn_fetch_subjects"), type="primary", use_container_width=True)
        with b2:
            clear = st.button(tr("btn_clear_cache"), use_container_width=True)

        st.markdown("---")
        filtro = st.text_input(tr("label_filter"), value=str(st.session_state.get("mg_filter", "")))
        st.session_state["mg_filter"] = filtro

    if clear:
        for k in ["assuntos_records", "assuntos_df", "assuntos_df_original", "assuntos_debug_pages"]:
            st.session_state.pop(k, None)
        st.rerun()

    if fetch:
        prog = st.progress(0)
        status = st.empty()
        status.info("Buscando...")

        sess = requests.Session()
        records, debug_pages = listar_assuntos_todos(
            cfg, rp=int(rp), max_pages=int(max_pages), max_total=int(max_total), session=sess
        )
        st.session_state["assuntos_debug_pages"] = debug_pages

        if not records:
            st.warning("Nenhum assunto retornado, ou falha na listagem.")
            with st.expander("Debug da listagem"):
                st.json(debug_pages)
            return

        df = pd.DataFrame(records)
        if "id" not in df.columns:
            st.error("Resposta sem coluna 'id'.")
            with st.expander("Debug da listagem"):
                st.json(debug_pages)
            return

        # normaliza tudo para string (exceto seleção)
        for col in df.columns:
            if col == "id":
                df[col] = df[col].astype(str)
            else:
                df[col] = df[col].apply(normalize_value)

        if "selecionar" not in df.columns:
            df.insert(0, "selecionar", False)
        df["selecionar"] = df["selecionar"].map(parse_bool_value).astype(bool)

        st.session_state["assuntos_records"] = records
        st.session_state["assuntos_df_original"] = df.drop(columns=["selecionar"], errors="ignore").copy(deep=True)
        st.session_state["assuntos_df"] = df

        prog.progress(100)
        status.success("Ok.")
        st.success(tr("msg_loaded_n").format(n=len(df)))

    df = st.session_state.get("assuntos_df")
    df_original = st.session_state.get("assuntos_df_original")

    # garante que "selecionar" seja booleano (checkbox)
    if isinstance(df, pd.DataFrame) and "selecionar" in df.columns:
        df["selecionar"] = df["selecionar"].map(parse_bool_value).astype(bool)

    if df is None or df_original is None:
        st.info(tr("msg_no_data_manage"))
        return

    # colunas exibidas
    defaults = [c for c in ["selecionar", "id", "assunto", "ativo", "descricao"] if c in df.columns]
    cols = st.multiselect(tr("label_columns"), options=list(df.columns), default=defaults, key="mg_cols")

    view = df.copy()
    filtro = str(st.session_state.get("mg_filter", "") or "")
    if filtro.strip():
        ft = filtro.strip().lower()
        mask = view.apply(lambda r: any(ft in str(v).lower() for v in r.values), axis=1)
        view = view.loc[mask]

    if cols:
        view = view[cols]

    st.markdown("### Lista de assuntos")
    edited = st.data_editor(
        view,
        use_container_width=True,
        height=520,
        num_rows="fixed",
        key="editor_assuntos",
        column_config={"selecionar": st.column_config.CheckboxColumn("selecionar")},
    )

    # ----------------------------
    # Reconcilia a edição (subconjunto) com o DF completo
    # ----------------------------
    full = df.copy()
    if "id" in edited.columns and "id" in full.columns:
        full_idx = full.set_index("id", drop=False)
        edited_idx = edited.set_index("id", drop=False)
        for rid, row in edited_idx.iterrows():
            if rid in full_idx.index:
                for col in edited_idx.columns:
                    full_idx.at[rid, col] = row[col]
        df_full_updated = full_idx.reset_index(drop=True)
    else:
        df_full_updated = edited.copy()

    if "selecionar" in df_full_updated.columns:
        df_full_updated["selecionar"] = df_full_updated["selecionar"].map(parse_bool_value).astype(bool)
    st.session_state["assuntos_df"] = df_full_updated

    # ----------------------------
    # Sessão: ações (seleção / edição em massa / salvar)
    # ----------------------------
    st.markdown("---")
    st.subheader("Ações")

    cS1, cS2, cS3, cS4 = st.columns([1, 1, 2, 2])
    with cS1:
        sel_count = int(df_full_updated["selecionar"].map(parse_bool_value).sum()) if "selecionar" in df_full_updated.columns else 0
        st.metric(tr("label_selected"), sel_count)

    with cS2:
        if st.button(tr("btn_select_all_filtered")):
            ids_visible = edited["id"].astype(str).tolist() if "id" in edited.columns else []
            tmp = df_full_updated.copy()
            if "id" in tmp.columns and "selecionar" in tmp.columns:
                tmp["selecionar"] = tmp.apply(lambda r: True if str(r["id"]) in ids_visible else bool(r["selecionar"]), axis=1)
                st.session_state["assuntos_df"] = tmp
                st.rerun()

        if st.button(tr("btn_clear_selection")):
            tmp = df_full_updated.copy()
            if "selecionar" in tmp.columns:
                tmp["selecionar"] = False
                st.session_state["assuntos_df"] = tmp
                st.rerun()

    with cS3:
        bulk_field = st.selectbox(tr("label_bulk_field"), options=[c for c in df_full_updated.columns if c not in ("selecionar",)], index=0)

    with cS4:
        if bulk_field in ("ativo", "mostra_hotsite", "mostrar_no_service"):
            bulk_value = st.selectbox(tr("label_bulk_value"), options=["S", "N"], index=0)
        else:
            bulk_value = st.text_input(tr("label_bulk_value"), value="")

    cB1, cB2 = st.columns([1, 3])
    with cB1:
        apply_bulk = st.button(tr("btn_apply_bulk"), use_container_width=True)
    with cB2:
        st.caption(tr("hint_bulk"))

    if apply_bulk:
        tmp = st.session_state["assuntos_df"].copy()
        ids_sel = tmp.loc[tmp["selecionar"].map(parse_bool_value), "id"].astype(str).tolist() if "selecionar" in tmp.columns else []
        if not ids_sel:
            st.warning(tr("msg_no_selection"))
        else:
            for rid in ids_sel:
                tmp.loc[tmp["id"].astype(str) == str(rid), bulk_field] = bulk_value
            st.session_state["assuntos_df"] = tmp
            st.success("Edição em massa aplicada.")
            st.rerun()

    st.markdown("---")
    cA, cB, cC, cD = st.columns([1, 1, 1, 2])
    with cA:
        only_changed = st.checkbox(tr("chk_save_only_changed"), value=True)
    with cB:
        validate_before = st.checkbox(tr("chk_validate_before_save"), value=True)
    with cC:
        save_only_selected = st.checkbox(tr("chk_save_only_selected"), value=True)
    with cD:
        salvar = st.button(tr("btn_save_put"), type="primary", use_container_width=True)

    if not salvar:
        return

    selected_ids = df_full_updated.loc[df_full_updated["selecionar"].map(parse_bool_value), "id"].astype(str).tolist() if "selecionar" in df_full_updated.columns else []

    orig_idx = df_original.set_index("id", drop=False)
    upd_idx = df_full_updated.drop(columns=["selecionar"], errors="ignore").set_index("id", drop=False)

    if save_only_selected and selected_ids:
        candidate_ids = [rid for rid in selected_ids if rid in upd_idx.index]
    else:
        candidate_ids = [rid for rid in upd_idx.index if rid in orig_idx.index]

    changed_ids: List[str] = []
    for rid in candidate_ids:
        if rid not in orig_idx.index:
            continue
        if not only_changed:
            changed_ids.append(rid)
            continue

        changed = False
        for col in upd_idx.columns:
            if col == "id":
                continue
            a = normalize_value(orig_idx.at[rid, col]) if col in orig_idx.columns else ""
            b = normalize_value(upd_idx.at[rid, col]) if col in upd_idx.columns else ""
            if a != b:
                changed = True
                break

        if changed:
            changed_ids.append(rid)

    if save_only_selected and selected_ids and not changed_ids:
        st.warning("Nenhum item selecionado sofreu alteração.")
        return
    if not changed_ids:
        st.info("Nenhuma alteração detectada.")
        return

    overlay = st.empty()
    overlay.markdown(dedent("""
        <style>
        .isp-overlay {
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.55);
            z-index: 99999;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .isp-overlay-card {
            background: rgba(20,20,24,0.92);
            border: 1px solid rgba(255,255,255,0.10);
            padding: 18px 22px;
            border-radius: 14px;
            min-width: 320px;
            max-width: 520px;
            box-shadow: 0 16px 60px rgba(0,0,0,0.55);
            text-align: center;
        }
        .isp-spinner {
            width: 42px;
            height: 42px;
            border-radius: 50%;
            border: 4px solid rgba(255,255,255,0.25);
            border-top-color: rgba(255,255,255,0.85);
            animation: ispSpin 0.9s linear infinite;
            margin: 0 auto 12px auto;
        }
        @keyframes ispSpin { to { transform: rotate(360deg);} }
        .isp-overlay-title { font-weight: 700; font-size: 16px; margin-bottom: 6px; }
        .isp-overlay-sub { opacity: 0.85; font-size: 13px; }
        section[data-testid="stSidebar"] hr { margin: 0.35rem 0 !important; }
section[data-testid="stSidebar"] .stButton { margin-bottom: 0.32rem !important; }
</style>
        <div class="isp-overlay">
          <div class="isp-overlay-card">
            <div class="isp-spinner"></div>
            <div class="isp-overlay-title">Salvando alterações…</div>
            <div class="isp-overlay-sub">Aguarde — a tela volta ao normal ao finalizar.</div>
          </div>
        </div>
        """), unsafe_allow_html=True)

    prog = st.progress(0)
    ok = 0
    err = 0
    results: List[dict] = []

    sess = requests.Session()
    try:
        for i, rid in enumerate(changed_ids, start=1):
            row = upd_idx.loc[rid].to_dict()

            base_payload: Dict[str, str] = {}
            for col in upd_idx.columns:
                if col == "id":
                    continue
                base_payload[col] = normalize_value(row.get(col, ""))

            if validate_before:
                v = validate_assunto(base_payload)
                if v:
                    err += 1
                    results.append({"id": rid, "status": "ERRO_VALIDACAO", "http_status": "", "mensagem": " | ".join(v)})
                    prog.progress(int(i / len(changed_ids) * 100))
                    continue

            resp = put_to_endpoint(cfg, f"{ENDPOINT_ASSUNTO}/{rid}", base_payload, session=sess)
            if resp.ok:
                ok += 1
                msg = ""
                if isinstance(resp.data, dict):
                    msg = str(resp.data.get("message") or resp.data.get("msg") or "")
                results.append({"id": rid, "status": "OK", "http_status": resp.http_status, "mensagem": msg})
            else:
                err += 1
                msg = resp.text
                if isinstance(resp.data, dict):
                    msg = str(resp.data.get("message") or resp.data.get("msg") or resp.data)
                results.append({"id": rid, "status": "ERRO", "http_status": resp.http_status, "mensagem": str(msg)[:1500]})

            prog.progress(int(i / len(changed_ids) * 100))
    finally:
        overlay.empty()

    st.success(tr("msg_finished").format(ok=ok, err=err))
    df_res = pd.DataFrame(results)
    st.dataframe(df_res, use_container_width=True, height=360)

    with st.expander("Debug da listagem (última busca)"):
        st.json(st.session_state.get("assuntos_debug_pages", []))



def page_diagnostics() -> None:
    import_page(
        page_title=tr("page_create_diagnostics_title"),
        endpoint_path=ENDPOINT_DIAGNOSTICO,
        name_col="descricao",
        validate_fn=validate_diagnostico,
        skip_label="Pular linhas com 'descricao' vazia",
        report_prefix="diagnosticos",
    )


# Router
key = st.session_state.page_key
if key == "home":
    page_home()
elif key == "subjects":
    page_subjects()
elif key == "manage_subjects":
    page_manage_subjects()
elif key == "diagnostics":
    page_diagnostics()
elif key == "settings":
    page_settings()
else:
    st.session_state.page_key = "home"
    st.rerun()

