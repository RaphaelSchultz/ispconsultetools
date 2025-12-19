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
# i18n
# ============================

I18N = {
    "pt-BR": {
        "app_name": "ISP Consulte Tools",
        "home": "Home",
        "create_subjects": "Criar Assuntos",
        "create_diagnostics": "Criar Diagnósticos",
        "settings": "Configurações",
        "page_home_title": "Home",
        "page_create_subjects_title": "Criar Assuntos",
        "page_create_diagnostics_title": "Criar Diagnósticos",
        "page_settings_title": "Configurações",
        "tab_auth": "Autenticação",
        "tab_personalization": "Personalização",
        "language": "Idioma",
        "theme": "Tema",
        "theme_auto": "Automático (sistema)",
        "theme_dark": "Escuro",
        "theme_light": "Claro",
        "session_only_note": "As configurações abaixo podem ser aplicadas **somente na sessão atual** (não salva em disco nem no navegador).",
        "host_label": "Host do IXC (IXC_BASE_URL)",
        "token_label": "Token Basic (IXC_AUTH_BASIC) — não é salvo",
        "cookie_label": "Cookie (IXC_COOKIE) — opcional",
        "timeout": "Timeout (seg)",
        "max_retries": "Max retries",
        "backoff": "Backoff (seg)",
        "apply_session": "💾 Aplicar (sessão)",
        "clear_overrides": "🧹 Limpar overrides",
        "test_auth": "🔎 Testar autenticação (HEAD)",
        "masked_summary": "Resumo (mascarado)",
        "auth_ok": "Autenticação OK (não retornou 401).",
        "auth_401": "401: credencial inválida ou cookie exigido. Se seu cURL usa IXC_Session, preencha o Cookie.",
        "auth_unknown": "Não deu para confirmar. Veja o JSON acima.",
        "project_info": "Informações do projeto",
        "what_can_do": "O que é possível fazer",
        "support": "Suporte",
        "go_create_subjects": "➡️ Ir para Criar Assuntos",
        "go_create_diagnostics": "➡️ Ir para Criar Diagnósticos",
        "status_config": "Status de autenticação/config (rápido)",
        "missing_config": "Falta configurar Host e/ou Token (use Configurações ou .env).",
        "present_config": "Host e token presentes (credenciais mascaradas).",
        "upload_xlsx": "Upload da planilha (.xlsx)",
        "summary": "Resumo",
        "preview_sheet": "Preview da planilha (primeiras linhas)",
        "run_create": "🚀 Criar no IXC",
        "run_validate": "✅ Apenas validar",
        "result": "Resultado",
        "created": "Criados/validados",
        "errors": "Erros",
        "downloads": "Downloads",
        "download_csv": "⬇️ Baixar relatório CSV",
        "download_json": "⬇️ Baixar compact_jsoncolumns (JSON)",
        "need_file": "Envie a planilha para começar.",
        "need_column": "A planilha precisa ter a coluna obrigatória: ",
        "templates": "Planilhas modelo",
        "download_template_subjects": "⬇️ Baixar modelo — Assuntos",
        "download_template_diagnostics": "⬇️ Baixar modelo — Diagnósticos",
        "template_missing": "Template não encontrado no projeto: ",
    },
    "en": {
        "app_name": "ISP Consulte Tools",
        "home": "Home",
        "create_subjects": "Create Subjects",
        "create_diagnostics": "Create Diagnostics",
        "settings": "Settings",
        "page_home_title": "Home",
        "page_create_subjects_title": "Create Subjects",
        "page_create_diagnostics_title": "Create Diagnostics",
        "page_settings_title": "Settings",
        "tab_auth": "Authentication",
        "tab_personalization": "Personalization",
        "language": "Language",
        "theme": "Theme",
        "theme_auto": "Auto (system)",
        "theme_dark": "Dark",
        "theme_light": "Light",
        "session_only_note": "Settings below are **session-only** (not saved to disk or browser).",
        "host_label": "IXC Host (IXC_BASE_URL)",
        "token_label": "Basic token (IXC_AUTH_BASIC) — not saved",
        "cookie_label": "Cookie (IXC_COOKIE) — optional",
        "timeout": "Timeout (sec)",
        "max_retries": "Max retries",
        "backoff": "Backoff (sec)",
        "apply_session": "💾 Apply (session)",
        "clear_overrides": "🧹 Clear overrides",
        "test_auth": "🔎 Test authentication (HEAD)",
        "masked_summary": "Masked summary",
        "auth_ok": "Auth OK (not 401).",
        "auth_401": "401: invalid credential or cookie required.",
        "auth_unknown": "Could not confirm. See JSON above.",
        "project_info": "Project info",
        "what_can_do": "What you can do",
        "support": "Support",
        "go_create_subjects": "➡️ Go to Create Subjects",
        "go_create_diagnostics": "➡️ Go to Create Diagnostics",
        "status_config": "Auth/config status (quick)",
        "missing_config": "Missing Host and/or Token (use Settings or .env).",
        "present_config": "Host and token present (masked).",
        "upload_xlsx": "Upload spreadsheet (.xlsx)",
        "summary": "Summary",
        "preview_sheet": "Spreadsheet preview (first rows)",
        "run_create": "🚀 Create in IXC",
        "run_validate": "✅ Validate only",
        "result": "Result",
        "created": "Created/validated",
        "errors": "Errors",
        "downloads": "Downloads",
        "download_csv": "⬇️ Download CSV report",
        "download_json": "⬇️ Download compact_jsoncolumns (JSON)",
        "need_file": "Upload the spreadsheet to start.",
        "need_column": "Spreadsheet must include required column: ",
        "templates": "Templates",
        "download_template_subjects": "⬇️ Download template — Subjects",
        "download_template_diagnostics": "⬇️ Download template — Diagnostics",
        "template_missing": "Template not found in project: ",
    },
}


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

  


def page_settings() -> None:
    st.title(tr("page_settings_title"))
    st.caption(tr("session_only_note"))

    tab_auth, tab_pers = st.tabs([f"🔐 {tr('tab_auth')}", f"🎨 {tr('tab_personalization')}"])

    with tab_auth:
        col1, col2 = st.columns([2, 2])

        with col1:
            base_url = st.text_input(tr("host_label"), value=cfg["base_url"], placeholder="https://ixc.seudominio.com.br")
            auth_basic = st.text_input(tr("token_label"), value=cfg["auth_basic"], type="password", placeholder="Basic abcdef... ou só abcdef...")
            cookie = st.text_input(tr("cookie_label"), value=cfg["cookie"], placeholder="IXC_Session=... (se necessário)")

        with col2:
            timeout_seconds = st.number_input(tr("timeout"), min_value=5.0, max_value=120.0, value=float(cfg["timeout_seconds"]))
            max_retries = st.number_input(tr("max_retries"), min_value=0, max_value=10, value=int(cfg["max_retries"]))
            retry_backoff_seconds = st.number_input(tr("backoff"), min_value=0.0, max_value=10.0, value=float(cfg["retry_backoff_seconds"]))

        c1, c2, c3 = st.columns([1, 1, 2])

        with c1:
            if st.button(tr("apply_session"), type="primary", use_container_width=True):
                st.session_state["cfg_base_url"] = (base_url or "").strip().rstrip("/")
                st.session_state["cfg_auth_basic"] = (auth_basic or "").strip()
                st.session_state["cfg_cookie"] = (cookie or "").strip()
                st.session_state["cfg_timeout_seconds"] = float(timeout_seconds)
                st.session_state["cfg_max_retries"] = int(max_retries)
                st.session_state["cfg_retry_backoff_seconds"] = float(retry_backoff_seconds)
                st.success("Config aplicada na sessão atual.")

        with c2:
            if st.button(tr("clear_overrides"), use_container_width=True):
                for k in [
                    "cfg_base_url",
                    "cfg_auth_basic",
                    "cfg_cookie",
                    "cfg_timeout_seconds",
                    "cfg_max_retries",
                    "cfg_retry_backoff_seconds",
                ]:
                    st.session_state.pop(k, None)
                st.success("Overrides removidos. Voltou para o .env.")
                st.rerun()

        with c3:
            st.write("**" + tr("masked_summary") + "**")
            cfg_now = get_runtime_config()
            token_mask = mask_middle((cfg_now["auth_basic"] or "").replace("Basic ", "").replace("basic ", "").strip())
            cookie_mask = "(vazio)" if not cfg_now["cookie"] else mask_middle(cfg_now["cookie"], 6, 4)
            st.code("\n".join([f"IXC_BASE_URL={cfg_now['base_url']}", f"IXC_AUTH_BASIC={token_mask}", f"IXC_COOKIE={cookie_mask}"]))

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
elif key == "diagnostics":
    page_diagnostics()
elif key == "settings":
    page_settings()
else:
    st.session_state.page_key = "home"
    st.rerun()
