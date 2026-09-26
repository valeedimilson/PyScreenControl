# PyScreenControl

Aplicativo gratuito para **visualização e controle de uma segunda tela no Windows**.

O PyScreenControl foi desenvolvido para situações em que um computador utiliza uma configuração de **tela estendida**, permitindo visualizar e controlar o conteúdo exibido em outro monitor ou projetor diretamente pela tela principal.

## ✨ Recursos

* 🖥️ Visualização da segunda tela em tempo real
* 🎥 Captura utilizando `mss`
* ⚡ Baixa latência e atualização de até 120 FPS
* 🖱️ Controle do mouse através da pré-visualização
* 🖱️ Clique esquerdo, direito e duplo clique
* 🖱️ Rolagem do mouse
* 🖥️ Seleção do monitor a ser capturado
* 🎚️ Controle da taxa de atualização
* 📌 Opção de manter a janela sempre no topo
* 📊 Exibição do FPS real da captura
* 🖼️ Interface adaptada para aproveitar a maior área possível da tela
* 🐍 Desenvolvido em Python
* 🪟 Compatível com Windows

---

## 🎯 Objetivo

O projeto foi criado principalmente para ambientes onde um computador possui uma segunda tela conectada, como:

* Projetores
* TVs
* Monitores secundários
* Salas de aula
* Auditórios
* Salas de reunião
* Apresentações

Por exemplo, em um auditório:

```text

┌───────────────────┐
│                   │
│   MONITOR 1       │
│   Computador      │
│                   │
└───────────────────┘
          │
          │ Tela estendida
          ▼
┌───────────────────┐
│                   │
│   MONITOR 2       │
│   PROJETOR        │
│                   │
└───────────────────┘
```

O PyScreenControl permite visualizar o conteúdo do **Monitor 2 dentro de uma janela do Monitor 1**.

---

## 🛠️ Tecnologias utilizadas

* [Python](https://www.python.org/)
* [PySide6](https://doc.qt.io/qtforpython/)
* [MSS](https://python-mss.readthedocs.io/)
* [PyWin32](https://github.com/mhammond/pywin32)
* [pyInstaller](https://pyinstaller.org/)

### Interface

A interface gráfica é construída utilizando **PySide6**, baseado no Qt.

### Captura de tela

A captura é realizada através do **MSS**, evitando conversões desnecessárias de imagem para manter a latência baixa.

### Controle do Windows

O projeto utiliza APIs do Windows através do **PyWin32** para movimentação e interação com o mouse.

---

## 📋 Requisitos

### Para executar o código-fonte

* Windows 10 ou superior
* Python 3.10 ou superior
* Conexão com o segundo monitor/projetor
* Ambiente de tela estendida configurado no Windows

---

## 🚀 Executando o projeto

Clone ou copie o projeto:

```bash
git clone https://github.com/valeedimilson/PyScreenControl.git
```

Entre na pasta:

```bash
cd PyScreenControl
```

Inicie o ambiente virtual com:

```bash
python -m venv .venv
```

Instale as dependências com:

```bash
pip install -r requirements.txt
```

Execute:

```bash
python main.py
```

---

## 📁 Estrutura do projeto

```text
PyScreenControl/
│
├── main.py
├── README.md
│
├── assets/
│   ├── logo.ico
│   └── logo.jpeg
│
└── ...
```

### `main.py`

Arquivo principal da aplicação.

### `assets/logo.ico`

Ícone utilizado pelo aplicativo e pelo executável.

### `assets/logo.jpeg`

Logo apresentada na tela inicial do aplicativo.

---

## 🖥️ Utilização

### 1. Configure o Windows

No Windows, configure os monitores como:

**Configurações → Sistema → Tela → Estender estes vídeos**

ou utilize:

```text
Win + P
```

e selecione:

```text
Estender
```

---

### 2. Abra o PyScreenControl

Ao iniciar, o programa apresenta a tela inicial:

```text
        [ LOGO ]

     PyScreenControl

Visualização e controle
    de segunda tela
```

---

### 3. Selecione o monitor

Utilize o campo:

```text
Monitor: [ Monitor 2 ]
```

para selecionar a tela que será visualizada.

---

### 4. Configure o FPS

O aplicativo permite selecionar uma taxa de atualização entre:

```text
15 FPS → 120 FPS
```

O valor padrão é:

```text
60 FPS
```

Taxas maiores podem aumentar o consumo de CPU/GPU.

---

### 5. Inicie a captura

Clique em:

```text
Iniciar
```

A tela inicial será substituída pela pré-visualização do monitor selecionado.

---

## 🖱️ Controle remoto do mouse

O PyScreenControl possui dois modos:

### Somente visualização

A segunda tela é apenas exibida.

```text
Somente visualização
```

Nenhuma interação com o mouse é enviada para o monitor capturado.

### Controle pela janela

Permite utilizar a pré-visualização para controlar o mouse.

```text
Controle pela janela
```

São suportados:

* Movimento
* Clique esquerdo
* Clique direito
* Duplo clique
* Botão do meio
* Rolagem

> **Observação:** o controle de mouse utiliza APIs de entrada do Windows. Alguns aplicativos executados com privilégios elevados ou interfaces específicas do Windows podem apresentar limitações.

---

## 📌 Sempre no topo

A opção:

```text
Sempre no topo
```

mantém a janela do PyScreenControl acima das outras janelas.

Isso pode ser útil durante apresentações ou quando o operador precisa acompanhar constantemente a segunda tela.

---

# 📦 Compilação

O projeto utiliza **PyInstaller** para gerar a versão executável para Windows.

## Instalar o PyInstaller

```bash
python -m pip install -U pyinstaller
```

Verifique:

```bash
python -m pyinstaller --version
```

---

## Compilação Standalone

A versão `standalone` gera uma pasta contendo o executável e todas as dependências necessárias.

Execute:

```bash
python -m PyInstaller --noconfirm --clean --windowed --onefile --name PyScreenControl --icon "assets\logo.ico" --add-data "assets;assets" main.py
```

O resultado será semelhante a:

```text
dist/
└─ main.exe
├── assets/
│   ├── logo.ico
│   └── logo.jpeg
└── ...
```

Execute:

```bash
dist\main.exe
```


O executável pode então ser distribuído para outros computadores Windows sem a necessidade de instalar Python.

---

# 🔧 Desenvolvimento

Para executar durante o desenvolvimento:

```bash
python main.py
```

Para testar alterações rapidamente, recomenda-se executar o código-fonte antes de realizar uma nova compilação com pyInstaller.

---

# ⚠️ Limitações conhecidas

O projeto está em desenvolvimento e algumas situações podem apresentar limitações.

Entre elas:

* Aplicativos executados como administrador podem não responder ao controle de mouse dependendo do nível de privilégio.
* Algumas interfaces do Windows podem utilizar mecanismos de entrada diferentes dos eventos tradicionais de mouse.
* A captura em FPS muito alto pode aumentar o consumo de recursos.
* O desempenho depende da resolução do monitor capturado e do hardware utilizado.
* A funcionalidade foi desenvolvida especificamente para Windows.

---

# 🗺️ Roadmap

Possíveis melhorias futuras:

* [ ] Controle de mouse utilizando `SendInput`
* [ ] Melhor controle de aplicativos executados como administrador
* [ ] Suporte a atalhos de teclado
* [ ] Controle completo de teclado
* [ ] Seleção automática do projetor
* [ ] Detecção automática de alteração de monitores
* [ ] Controle de escala da pré-visualização
* [ ] Indicador de latência
* [ ] Otimizações adicionais de CPU
* [ ] Instalador para Windows
* [ ] Atualização automática
* [ ] Configurações persistentes
* [ ] Modo tela cheia
* [ ] Atalho para iniciar/parar captura

---

# 🤝 Contribuição

Contribuições são bem-vindas.

Para contribuir:

1. Faça um fork do projeto.
2. Crie uma branch para sua alteração.
3. Faça as modificações.
4. Teste no Windows.
5. Envie um Pull Request.

---

# 📄 Licença

Este projeto é disponibilizado gratuitamente.

A licença definitiva do projeto ainda deverá ser definida.

---

# 👨‍💻 Autor

**valeedimilson**

Projeto desenvolvido com foco em utilização prática em ambientes educacionais e apresentações.

---

## 💡 Motivação

O PyScreenControl nasceu de uma necessidade prática:

> Visualizar e controlar o conteúdo de um projetor conectado como segunda tela sem precisar olhar diretamente para a tela de projeção.

A proposta é manter o projeto **gratuito, simples e acessível**, podendo ser utilizado em escolas, auditórios, salas de aula e outros ambientes que utilizem múltiplas telas.
