# ISP Consulte Tools — IXC Importador

## Requisitos
- Python 3.10+ (recomendado)
- Acesso ao IXC (Host + Token)
- (Opcional) Cookie `IXC_Session` se sua instalação exigir

## Rodar no macOS / Linux
```bash
cd ixc_assuntos_uploader
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Rodar no Windows (PowerShell)
```powershell
cd ixc_assuntos_uploader
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Configuração (.env)
Copie `.env.example` para `.env` e preencha as variáveis.
> Dica: você pode usar o Token “cru” no formato `17:...` na tela **Configurações**; o sistema converte para Basic automaticamente.

## Problemas comuns
- **`No module named streamlit`**: você não instalou os requirements na venv.
- **`No module named dotenv`**: instale `python-dotenv` ou rode `pip install -r requirements.txt`.
