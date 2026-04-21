# Sistema de Gestão EFITA

Um sistema completo de gestão de inscrições e administração para o evento EFITA. O projeto é dividido em um backend robusto (FastAPI) e um frontend ágil (Vite + Vanilla JS).

## 🚀 Funcionalidades

### Área do Participante
- **Inscrição**: Formulário para registro de novos participantes.
- **Consulta de Status**: Página para os participantes consultarem o status de sua inscrição (Pendente, Aprovada, Paga, etc.) através do email e CPF.

### Área Administrativa
- **Autenticação**: Login seguro (JWT) para administradores.
- **Dashboard**: Painel de controle para visualizar todas as inscrições.
- **Ações**: Capacidade de aprovar inscrições, marcar como pagas e realizar outras alterações de status.

## 🛠️ Tecnologias Utilizadas

### Backend
- **Python 3.10+**
- **FastAPI** (Framework Web assíncrono de alta performance)
- **SQLAlchemy** (ORM para comunicação com o banco de dados)
- **SQLite** (Banco de dados)
- **Pydantic** (Validação de dados)
- **python-jose** e **bcrypt** (Autenticação JWT e Hash de senhas)
- **pytest** (Testes automatizados)

### Frontend
- **HTML5 & CSS3** (Estilização pura para máxima performance e controle)
- **Vanilla JavaScript** (Lógica do cliente sem frameworks pesados)
- **Vite** (Build tool e servidor de desenvolvimento super rápido)

## 📁 Estrutura do Projeto

```
gestao-efita2/
├── backend/                # Aplicação da API REST
│   ├── app/                # Código fonte do backend
│   │   ├── routers/        # Rotas da API (admin, participantes, auth)
│   │   ├── schemas/        # Modelos Pydantic (validação)
│   │   ├── models.py       # Modelos SQLAlchemy (banco de dados)
│   │   ├── crud.py         # Lógica de acesso ao banco
│   │   └── main.py         # Ponto de entrada FastAPI
│   ├── tests/              # Testes unitários e de integração (pytest)
│   ├── .env.example        # Exemplo de variáveis de ambiente
│   ├── requirements.txt    # Dependências do Python
│   ├── efita.db            # Banco de dados SQLite
│   └── run.py              # Script para rodar o servidor
├── frontend/               # Aplicação Web (Cliente)
│   ├── public/             # Arquivos estáticos
│   ├── src/                # Código fonte JavaScript (api.js, main.js)
│   ├── styles/             # Arquivos CSS
│   ├── admin/              # Páginas do painel administrativo
│   ├── index.html          # Página de inscrição principal
│   ├── consulta.html       # Página de consulta de status
│   ├── package.json        # Dependências do Node.js
│   └── vite.config.js      # Configuração do Vite
└── README.md               # Esta documentação
```

## ⚙️ Pré-requisitos

Certifique-se de ter os seguintes itens instalados no seu ambiente local:
- [Python 3.10+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/) (inclui npm)

## 🔧 Instalação e Configuração

Você pode executar o projeto de forma simplificada utilizando Docker, ou configurando os ambientes manualmente.

### 🐳 Rodando com Docker (Recomendado)

Certifique-se de ter o [Docker](https://docs.docker.com/get-docker/) e o Docker Compose instalados.

1. Na raiz do projeto, execute o comando para construir as imagens e subir os containers em segundo plano:
   ```bash
   docker-compose up --build -d
   ```

2. Acesse os serviços:
   - **Frontend**: [http://localhost:8080](http://localhost:8080)
   - **Backend API**: [http://localhost:8000](http://localhost:8000)
   - **Documentação da API (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)

3. Para parar e remover os containers, execute:
   ```bash
   docker-compose down
   ```

*(Nota: O banco de dados SQLite será persistido automaticamente em um volume Docker local).*

---

### 💻 Rodando Manualmente

Siga os passos abaixo se preferir rodar os serviços individualmente sem o Docker.

#### 1. Configurando o Backend

Navegue até a pasta do backend:
```bash
cd backend
```

Crie e ative um ambiente virtual (recomendado):
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

Instale as dependências:
```bash
pip install -r requirements.txt
```

Configure as variáveis de ambiente:
Copie o arquivo de exemplo e edite conforme necessário:
```bash
cp .env.example .env
```

Gere a conta de administrador inicial (Opcional, mas necessário para acesso ao painel):
```bash
python seed_admin.py
# Ou utilize o force_seed.py se precisar sobrescrever a base
python force_seed.py
```

Inicie o servidor de desenvolvimento:
```bash
python run.py
# O backend estará rodando em http://localhost:8000
# A documentação da API pode ser acessada em http://localhost:8000/docs
```

#### 2. Configurando o Frontend

Abra um novo terminal e navegue até a pasta do frontend:
```bash
cd frontend
```

Instale as dependências do Node:
```bash
npm install
```

Inicie o servidor de desenvolvimento Vite:
```bash
npm run dev
# O frontend estará disponível (geralmente) em http://localhost:5173
```

## 🧪 Rodando os Testes

Para garantir que tudo está funcionando corretamente, você pode rodar a suíte de testes automatizados do backend.

No diretório `backend` (com o ambiente virtual ativado), execute:
```bash
pytest tests/ -v
```

## 📝 Regras do Projeto (Contrato de Desenvolvimento)

- **Cobertura de Testes**: Nenhuma alteração de código deve ser integrada sem a cobertura de testes correspondente. Novas funcionalidades exigem testes (unidade/integração) cobrindo os cenários de sucesso e falha. Correções de bugs exigem a criação prévia de um teste que reproduza a falha reportada.
