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
import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv



# ============================
# .env + defaults (PRECISA vir antes do session_state init)
# ============================
load_dotenv()

ENV_IXC_BASE_URL = (os.getenv("IXC_BASE_URL", "") or "").strip().rstrip("/")
ENV_IXC_AUTH_BASIC = (os.getenv("IXC_AUTH_BASIC", "") or "").strip()
ENV_IXC_COOKIE = (os.getenv("IXC_COOKIE", "") or "").strip()
ENV_IXC_TIMEOUT_SECONDS = float(os.getenv("IXC_TIMEOUT_SECONDS", "30"))
ENV_IXC_MAX_RETRIES = int(os.getenv("IXC_MAX_RETRIES", "3"))
ENV_IXC_RETRY_BACKOFF_SECONDS = float(os.getenv("IXC_RETRY_BACKOFF_SECONDS", "1.5"))

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
        'what_can_do': 'What you can do'},
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
           'token_label': 'Token Basic (IXC_AUTH_BASIC) — sessão (não salva em disco)',
           'upload_xlsx': 'Upload da planilha (.xlsx)',
           'what_can_do': 'O que é possível fazer'}}


def tr(key: str) -> str:
    lang = st.session_state.get("lang", "pt-BR")
    return I18N.get(lang, I18N["pt-BR"]).get(key, key)


# ============================
# Streamlit config + session defaults
# ============================

st.set_page_config(page_title="ISP Consulte Tools", layout="wide")

if "lang" not in st.session_state:
    st.session_state.lang = "pt-BR"

# theme_mode: auto | dark | light
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "auto"

if "page_key" not in st.session_state:
    st.session_state.page_key = "home"  # home | subjects | diagnostics | settings

# Config aplicada (sessão). Se existir .env, nasce daqui; senão, fica vazio até você aplicar na tela.
if "cfg_base_url" not in st.session_state:
    st.session_state['cfg_base_url'] = (ENV_IXC_BASE_URL or "").strip().rstrip("/")
if "cfg_auth_basic" not in st.session_state:
    st.session_state['cfg_auth_basic'] = (ENV_IXC_AUTH_BASIC or "").strip()
if "cfg_cookie" not in st.session_state:
    st.session_state['cfg_cookie'] = (ENV_IXC_COOKIE or "").strip()
if "cfg_timeout_seconds" not in st.session_state:
    st.session_state['cfg_timeout_seconds'] = float(ENV_IXC_TIMEOUT_SECONDS)
if "cfg_max_retries" not in st.session_state:
    st.session_state['cfg_max_retries'] = int(ENV_IXC_MAX_RETRIES)
if "cfg_retry_backoff_seconds" not in st.session_state:
    st.session_state['cfg_retry_backoff_seconds'] = float(ENV_IXC_RETRY_BACKOFF_SECONDS)



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
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] { height: 100vh; }
section[data-testid="stSidebar"] div.stVerticalBlock { display:flex; flex-direction:column; height: 100vh; }
.sidebar-title { text-align:center; font-weight:800; font-size:20px; margin-top:0.25rem; margin-bottom:0.35rem; }
section[data-testid="stSidebar"] .stButton>button{
  border-radius: 12px !important;
  border: 1px solid var(--border) !important;
  background: var(--panel) !important;
  padding: 0.72rem 0.92rem !important;
  text-align: left !important;
  justify-content: flex-start !important;
}
section[data-testid="stSidebar"] .stButton>button:hover{
  border-color: var(--border2) !important;
  background: var(--panel2) !important;
}
section[data-testid="stSidebar"] div.stVerticalBlock > div:has(.sidebar-flex-spacer) { flex: 1 1 auto; }
/* fallback: spacer usually ends up around this position; keep it generous */
section[data-testid="stSidebar"] div.stVerticalBlock > div:nth-child(7) { flex: 1 1 auto; }
.sidebar-flex-spacer { height: 1px; }
div[data-testid="stTabs"] button[role="tab"]{ border-radius: 10px 10px 0 0 !important; }
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


ENDPOINT_ASSUNTO = "/webservice/v1/su_oss_assunto"
ENDPOINT_DIAGNOSTICO = "/webservice/v1/su_diagnostico"


def _sanitize(v: str) -> str:
    v = (v or "").strip()
    for _ in range(3):
        v = v.strip().strip('"').strip("'").strip()
    return v


def mask_middle(s: str, keep_left: int = 10, keep_right: int = 6) -> str:
    s = s or ""
    if len(s) <= keep_left + keep_right + 3:
        return "*" * len(s)
    return s[:keep_left] + "..." + s[-keep_right:]


def get_runtime_config() -> Dict[str, Any]:
    base_url = st.session_state.get("cfg_base_url", "")
    auth = st.session_state.get("cfg_auth_basic", "")
    cookie = st.session_state.get("cfg_cookie", "")
    return {
        "base_url": (base_url or "").strip().rstrip("/"),
        "auth_basic": (auth or "").strip(),
        "cookie": (cookie or "").strip(),
        "timeout_seconds": float(st.session_state.get("cfg_timeout_seconds", ENV_IXC_TIMEOUT_SECONDS)),
        "max_retries": int(st.session_state.get("cfg_max_retries", ENV_IXC_MAX_RETRIES)),
        "retry_backoff_seconds": float(st.session_state.get("cfg_retry_backoff_seconds", ENV_IXC_RETRY_BACKOFF_SECONDS)),
    }


def build_headers(cfg: Dict[str, Any]) -> Dict[str, str]:
    if not cfg.get("base_url") or not cfg.get("auth_basic"):
        return {}
    auth = _sanitize(cfg["auth_basic"])
    if not auth.lower().startswith("basic "):
        auth = f"Basic {auth}"
    headers = {"Content-Type": "application/json", "Authorization": auth}
    cookie = _sanitize(cfg.get("cookie") or "")
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


def test_auth(cfg: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{cfg['base_url']}{ENDPOINT_ASSUNTO}"  # endpoint conhecido para HEAD
    headers = build_headers(cfg)
    try:
        resp = requests.request("HEAD", url, headers=headers, timeout=cfg["timeout_seconds"])
        return {
            "ok": resp.status_code != 401,
            "status_code": resp.status_code,
            "response_headers": dict(resp.headers),
            "response_text": (resp.text or "")[:500],
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def post_to_endpoint(cfg: Dict[str, Any], endpoint_path: str, payload: Dict[str, str]) -> IXCResponse:
    url = f"{cfg['base_url']}{endpoint_path}"
    headers = build_headers(cfg)

    last_text = ""
    last_data: Optional[dict] = None
    last_status: Optional[int] = None

    for attempt in range(1, cfg["max_retries"] + 1):
        try:
            resp = requests.post(
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


def put_to_endpoint(cfg: Dict[str, Any], endpoint_path: str, payload: Dict[str, str]) -> IXCResponse:
    url = f"{cfg['base_url']}{endpoint_path}"
    headers = build_headers(cfg)

    last_text = ""
    last_data: Optional[dict] = None
    last_status: Optional[int] = None

    for attempt in range(1, cfg["max_retries"] + 1):
        try:
            resp = requests.put(
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


def listar_assuntos_todos(cfg: Dict[str, Any], rp: int = 1000, max_pages: int = 50, max_total: int = 0) -> Tuple[List[dict], List[dict]]:
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
                resp = requests.request(
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

st.sidebar.markdown(f"<div class='sidebar-title'>{tr('app_name')}</div>", unsafe_allow_html=True)
st.sidebar.markdown("---")

if st.sidebar.button("🏠 " + tr("home"), use_container_width=True):
    set_page("home")

if st.sidebar.button("🧾 " + tr("create_subjects"), use_container_width=True):
    set_page("subjects")

if st.sidebar.button("📝 " + tr("manage_subjects"), use_container_width=True):
    set_page("manage_subjects")

if st.sidebar.button("🩺 " + tr("create_diagnostics"), use_container_width=True):
    set_page("diagnostics")

st.sidebar.markdown("<div class='sidebar-flex-spacer'></div>", unsafe_allow_html=True)

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

    c1, c2 = st.columns(2)
    with c1:
        if st.button(tr("go_create_subjects"), type="primary"):
            set_page("subjects")
    with c2:
        if st.button(tr("go_create_diagnostics")):
            set_page("diagnostics")


def page_settings() -> None:
    st.title(tr("page_settings_title"))
    st.caption(tr("session_only_note"))

    cfg = get_runtime_config()

    # Campos (rascunho) da tela. Só viram 'config aplicada' quando você clicar em Aplicar.
    if "ui_base_url" not in st.session_state:
        st.session_state['ui_base_url'] = cfg["base_url"]
    if "ui_auth_basic" not in st.session_state:
        st.session_state['ui_auth_basic'] = cfg["auth_basic"]
    if "ui_cookie" not in st.session_state:
        st.session_state['ui_cookie'] = cfg["cookie"]
    if "ui_timeout_seconds" not in st.session_state:
        st.session_state['ui_timeout_seconds'] = float(cfg["timeout_seconds"])
    if "ui_max_retries" not in st.session_state:
        st.session_state['ui_max_retries'] = int(cfg["max_retries"])
    if "ui_retry_backoff_seconds" not in st.session_state:
        st.session_state['ui_retry_backoff_seconds'] = float(cfg["retry_backoff_seconds"])

    draft_cfg = {
        "base_url": (st.session_state.get("ui_base_url") or "").strip().rstrip("/"),
        "auth_basic": (st.session_state.get("ui_auth_basic") or "").strip(),
        "cookie": (st.session_state.get("ui_cookie") or "").strip(),
        "timeout_seconds": float(st.session_state.get("ui_timeout_seconds", cfg["timeout_seconds"])),
        "max_retries": int(st.session_state.get("ui_max_retries", cfg["max_retries"])),
        "retry_backoff_seconds": float(st.session_state.get("ui_retry_backoff_seconds", cfg["retry_backoff_seconds"])),
    }

    tab_auth, tab_pers = st.tabs([f"🔐 {tr('tab_auth')}", f"🎨 {tr('tab_personalization')}"])

    with tab_auth:
        col1, col2 = st.columns([2, 2])

        with col1:
            base_url = st.text_input(tr("host_label"), key="ui_base_url", placeholder="https://ixc.seudominio.com.br")
            auth_basic = st.text_input(tr("token_label"), key="ui_auth_basic", type="password", placeholder="Basic abcdef... ou só abcdef...")
            cookie = st.text_input(tr("cookie_label"), key="ui_cookie", placeholder="IXC_Session=... (se necessário)")

        with col2:
            timeout_seconds = st.number_input(tr("timeout"), key="ui_timeout_seconds", min_value=5.0, max_value=120.0, value=float(st.session_state['ui_timeout_seconds']))
            max_retries = st.number_input(tr("max_retries"), key="ui_max_retries", min_value=0, max_value=10, value=int(st.session_state['ui_max_retries']))
            retry_backoff_seconds = st.number_input(tr("backoff"), key="ui_retry_backoff_seconds", min_value=0.0, max_value=10.0, value=float(st.session_state['ui_retry_backoff_seconds']))

    st.markdown('---')
    c_apply1, c_apply2 = st.columns([1, 1])
    with c_apply1:
        if st.button('💾 Aplicar (sessão)', type='primary', use_container_width=True):
            st.session_state['cfg_base_url'] = (st.session_state['ui_base_url'] or '').strip().rstrip('/')
            st.session_state['cfg_auth_basic'] = (st.session_state['ui_auth_basic'] or '').strip()
            st.session_state['cfg_cookie'] = (st.session_state['ui_cookie'] or '').strip()
            st.session_state['cfg_timeout_seconds'] = float(st.session_state['ui_timeout_seconds'])
            st.session_state['cfg_max_retries'] = int(st.session_state['ui_max_retries'])
            st.session_state['cfg_retry_backoff_seconds'] = float(st.session_state['ui_retry_backoff_seconds'])
            st.success('Configuração aplicada para esta sessão (não salva em disco).')
    with c_apply2:
        if st.button('🧹 Restaurar do .env', use_container_width=True):
            st.session_state['ui_base_url'] = (ENV_IXC_BASE_URL or '').strip().rstrip('/')
            st.session_state['ui_auth_basic'] = (ENV_IXC_AUTH_BASIC or '').strip()
            st.session_state['ui_cookie'] = (ENV_IXC_COOKIE or '').strip()
            st.session_state['ui_timeout_seconds'] = float(ENV_IXC_TIMEOUT_SECONDS)
            st.session_state['ui_max_retries'] = int(ENV_IXC_MAX_RETRIES)
            st.session_state['ui_retry_backoff_seconds'] = float(ENV_IXC_RETRY_BACKOFF_SECONDS)
            st.info('Campos restaurados do .env (clique em Aplicar para usar).')

    c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
    with c1:
        rp = st.number_input(tr("label_rp"), min_value=1, max_value=5000, value=1000, step=1)
    with c2:
        max_pages = st.number_input(tr("label_max_pages"), min_value=1, max_value=200, value=50, step=1)
    with c3:
        max_total = st.number_input(tr("label_max_total"), min_value=0, max_value=1000000, value=0, step=1)
    with c4:
        st.write("**Endpoint:**")
        st.code(f"{draft_cfg['base_url']}{ENDPOINT_ASSUNTO}")

        st.markdown("---")
        if st.button(tr("test_auth")):
            r = test_auth(draft_cfg)
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
        if st.button('Ir para Configurações', type='primary'):
            set_page('settings')
        return

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        rp = st.number_input(tr("label_rp"), min_value=1, max_value=5000, value=1000, step=1)
    with c2:
        max_pages = st.number_input(tr("label_max_pages"), min_value=1, max_value=200, value=50, step=1)
    with c3:
        max_total = st.number_input(tr("label_max_total"), min_value=0, max_value=200000, value=0, step=1)

    st.write("**Endpoint:**")
    st.code(f"{cfg['base_url']}{ENDPOINT_ASSUNTO}")

    b1, b2 = st.columns([1, 1])
    with b1:
        fetch = st.button(tr("btn_fetch_subjects"), type="primary", use_container_width=True)
    with b2:
        clear = st.button(tr("btn_clear_cache"), use_container_width=True)

    if clear:
        for k in ["assuntos_records", "assuntos_df", "assuntos_df_original", "assuntos_debug_pages"]:
            st.session_state.pop(k, None)
        st.rerun()

    if fetch:
        prog = st.progress(0)
        status = st.empty()
        status.info("Buscando...")
        records, debug_pages = listar_assuntos_todos(cfg, rp=int(rp), max_pages=int(max_pages), max_total=int(max_total))
        st.session_state["assuntos_debug_pages"] = debug_pages

        if not records:
            st.warning("Nenhum assunto retornado, ou falha na listagem.")
            with st.expander("Debug da listagem"):
                st.json(debug_pages)
            return

        df = pd.DataFrame(records)
        if "id" not in df.columns:
            st.error("Não encontrei a coluna 'id' no retorno da API.")
            with st.expander("Debug da listagem"):
                st.json(debug_pages)
            return

        for col in df.columns:
            df[col] = df[col].map(normalize_value)

        if "selecionar" not in df.columns:
            df.insert(0, "selecionar", False)
        df["selecionar"] = df["selecionar"].map(parse_bool_value).astype(bool)

        st.session_state["assuntos_records"] = records
        st.session_state["assuntos_df_original"] = df.drop(columns=["selecionar"], errors="ignore").copy(deep=True)
        st.session_state["assuntos_df"] = df

        prog.progress(100)
        st.success(tr("msg_loaded_n").format(n=len(df)))

    df = st.session_state.get("assuntos_df")
    df_original = st.session_state.get("assuntos_df_original")

    # garante que "selecionar" seja booleano (checkbox) e não texto
    if isinstance(df, pd.DataFrame) and "selecionar" in df.columns:
        df["selecionar"] = df["selecionar"].map(parse_bool_value).astype(bool)

    if df is None or df_original is None:
        st.info(tr("msg_no_data_manage"))
        return

    filtro = st.text_input(tr("label_filter"), value="")

    defaults = [c for c in ["selecionar", "id", "assunto", "ativo", "descricao"] if c in df.columns]
    cols = st.multiselect(tr("label_columns"), options=list(df.columns), default=defaults)

    view = df.copy()
    if filtro.strip():
        ft = filtro.strip().lower()
        cols_f = [c for c in ["assunto", "descricao"] if c in view.columns]
        if cols_f:
            msk = False
            for c in cols_f:
                msk = msk | view[c].astype(str).str.lower().str.contains(ft, na=False)
            view = view[msk]

    if cols:
        if "selecionar" in df.columns and "selecionar" not in cols:
            cols = ["selecionar"] + cols
        if "id" in df.columns and "id" not in cols:
            cols = ["id"] + cols
        view = view[cols]

    if "selecionar" in view.columns:
        view["selecionar"] = view["selecionar"].map(parse_bool_value).astype(bool)
    edited = st.data_editor(
        view,
        use_container_width=True,
        height=560,
        column_config={"selecionar": st.column_config.CheckboxColumn("Selecionar")},
        disabled=["id"] if "id" in view.columns else [],
        num_rows="fixed",
        key="editor_manage_assuntos",
    )

    if "id" not in edited.columns:
        st.error(tr("msg_missing_id"))
        return

    # Reconcilia edits no DF completo
    df_full = df.copy()
    edited_idx = edited.set_index("id", drop=False)
    full_idx = df_full.set_index("id", drop=False)

    for col in edited.columns:
        if col == "id":
            continue
        for rid, val in edited_idx[col].items():
            if rid in full_idx.index:
                full_idx.at[rid, col] = parse_bool_value(val) if col == 'selecionar' else normalize_value(val)

    df_full_updated = full_idx.reset_index(drop=True)
    if "selecionar" in df_full_updated.columns:
        df_full_updated["selecionar"] = df_full_updated["selecionar"].map(parse_bool_value).astype(bool)
    st.session_state["assuntos_df"] = df_full_updated

    st.markdown("---")
    cS1, cS2, cS3, cS4 = st.columns([1, 1, 2, 2])

    with cS1:
        sel_count = int(df_full_updated['selecionar'].map(parse_bool_value).sum()) if 'selecionar' in df_full_updated.columns else 0
        st.metric(tr("label_selected"), sel_count)

    with cS2:
        if st.button(tr("btn_select_all_filtered")):
            ids_visible = edited["id"].tolist()
            tmp = df_full_updated.copy()
            tmp.loc[tmp["id"].isin(ids_visible), "selecionar"] = True
            st.session_state["assuntos_df"] = tmp
            st.rerun()

        if st.button(tr("btn_clear_selection")):
            tmp = df_full_updated.copy()
            if "selecionar" in tmp.columns:
                tmp["selecionar"] = False
            st.session_state["assuntos_df"] = tmp
            st.rerun()

    with cS3:
        bulk_field_options = [c for c in df_full_updated.columns if c not in ("id", "selecionar")]
        bulk_field = st.selectbox(tr("label_bulk_field"), options=bulk_field_options, index=bulk_field_options.index("ativo") if "ativo" in bulk_field_options else 0)

    with cS4:
        yesno_fields = {
            "ativo",
            "mostra_hotsite",
            "mostrar_no_service",
            "exige_comodato_finalizar_os",
            "exige_produto_finalizar_os",
            "diagnostico_obrigatorio_finalizacao_os",
            "localizacao_obrigatoria_cliente_finalizacao_os",
            "localizacao_obrigatoria_login_finalizacao_os",
            "contrato_obrigatorio",
            "sla_apenas_dias_uteis",
            "validar_choque_horarios_agendamento_os",
        }
        if bulk_field in yesno_fields:
            bulk_value = st.selectbox(tr("label_bulk_value"), options=["S", "N"], index=0)
        elif bulk_field == "tipo_comissao":
            bulk_value = st.selectbox(tr("label_bulk_value"), options=["F", "P"], index=0)
        elif bulk_field in ("layout_impressao", "numero_de_vias", "metas_horas_abertura_ticket", "quantidade_equipamentos", "quantidade_produtos"):
            bulk_value = str(st.number_input(tr("label_bulk_value"), min_value=0, value=0, step=1))
        else:
            bulk_value = st.text_input(tr("label_bulk_value"), value="")

    cB1, cB2 = st.columns([1, 3])
    with cB1:
        apply_bulk = st.button(tr("btn_apply_bulk"), use_container_width=True)
    with cB2:
        st.caption(tr("hint_bulk"))

    if apply_bulk:
        tmp = df_full_updated.copy()
        ids_sel = tmp.loc[tmp['selecionar'].map(parse_bool_value) == True, 'id'].astype(str).tolist() if 'selecionar' in tmp.columns else []
        if not ids_sel:
            st.warning(tr("msg_no_selection"))
        else:
            tmp.loc[tmp["id"].astype(str).isin(ids_sel), bulk_field] = normalize_value(bulk_value)
            st.session_state["assuntos_df"] = tmp
            st.success(tr("msg_bulk_applied").format(field=bulk_field, value=bulk_value, n=len(ids_sel)))
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

    selected_ids = df_full_updated.loc[df_full_updated['selecionar'].map(parse_bool_value) == True, 'id'].astype(str).tolist() if 'selecionar' in df_full_updated.columns else []

    orig_idx = df_original.set_index("id", drop=False)
    upd_idx = df_full_updated.drop(columns=["selecionar"], errors="ignore").set_index("id", drop=False)

    if save_only_selected and selected_ids:
        candidate_ids = [rid for rid in selected_ids if rid in upd_idx.index]
    else:
        candidate_ids = [rid for rid in upd_idx.index if rid in orig_idx.index]

    changed_ids = []
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

    if not changed_ids:
        st.info(tr("msg_nothing_to_save"))
        return

    records = st.session_state.get("assuntos_records") or []
    base_by_id = {normalize_value(r.get("id")): {str(k): normalize_value(v) for k, v in (r or {}).items()} for r in records if normalize_value(r.get("id"))}

    prog = st.progress(0)
    status = st.empty()
    results = []
    ok = 0
    err = 0

    for i, rid in enumerate(changed_ids, start=1):
        status.info(f"{tr('put_saving')} {i}/{len(changed_ids)} — id={rid}")

        base_payload = dict(base_by_id.get(str(rid)) or {})
        row = upd_idx.loc[rid]
        for col in upd_idx.columns:
            if col == "id":
                continue
            base_payload[col] = normalize_value(row[col])

        if validate_before:
            v = validate_assunto(base_payload)
            if v:
                err += 1
                results.append({"id": rid, "status": "ERRO_VALIDACAO", "http_status": "", "mensagem": " | ".join(v)})
                prog.progress(int(i / len(changed_ids) * 100))
                continue

        resp = put_to_endpoint(cfg, f"{ENDPOINT_ASSUNTO}/{rid}", base_payload)
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

    st.success(tr("msg_finished").format(ok=ok, err=err))
    df_res = pd.DataFrame(results)
    st.dataframe(df_res, use_container_width=True, height=360)

    st.download_button(tr("download_edit_csv"), data=df_res.to_csv(index=False).encode("utf-8-sig"), file_name="relatorio_edicao_assuntos.csv", mime="text/csv", use_container_width=True)
    st.download_button(tr("download_edit_json"), data=json.dumps(results, ensure_ascii=False, indent=2).encode("utf-8"), file_name="compact_edicao_assuntos.json", mime="application/json", use_container_width=True)

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