# 🖥️ Guia da Interface — ZPL Label Editor

Explicação completa de cada elemento da interface do ZPL Label Editor.

---

## Layout Geral

A interface é dividida em 4 áreas principais:

```
┌──────┬──────────────────────────────────────────────────────┐
│      │  Menu: Configurações > Preferências                  │
│  B   ├────────────────────┬─────────────────────────────────┤
│  A   │                    │                                 │
│  R   │  Editor de         │    Canvas de Preview            │
│  R   │  Código ZPL        │    (Visualização da etiqueta)   │
│  A   │                    │                                 │
│      ├────────────────────┤                                 │
│  L   │ Config. Etiqueta   │                                 │
│  A   │ [DPI][Unid][Larg]  ├─────────────────────────────────┤
│  T   │ [Atualizar Preview]│ [Movimento] [Grade] [Resolução] │
│  E   │                    │                                 │
│  R   │                    │                                 │
│  A   │                    │                                 │
│  L   │                    │                                 │
└──────┴────────────────────┴─────────────────────────────────┘
```

---

## 1. Barra Lateral (Ferramentas)

A barra lateral fica à esquerda e contém as ferramentas principais:

### 🔤 Botão "T" — Texto
- **O que faz:** Ativa o modo de criação de texto
- **Como usar:** Clique no botão e depois clique no canvas para inserir um elemento de texto na posição desejada
- **Resultado:** Insere um `^FO{x},{y}^A0N,30,30^FDTexto^FS` no código ZPL

### ║║║║ Botão "||||" — Código de Barras
- **O que faz:** Ativa o modo de criação de código de barras
- **Como usar:** Clique no botão e depois clique no canvas para inserir um código de barras
- **Resultado:** Insere um `^FO{x},{y}^BY2^BUN,80^FD0000000000^FS` no código ZPL

### ↖ Botão "Seleção"
- **O que faz:** Volta ao modo de seleção (cursor normal)
- **Como usar:** Clique para desativar qualquer ferramenta e voltar a poder selecionar/arrastar elementos
- **Resultado:** Desliga qualquer modo ativo

### ⟳ Botão "Converter"
- **O que faz:** Ativa o **modo de conversão** — a funcionalidade principal de arrastar e soltar
- **Como usar:**
  1. Clique no botão "Converter"
  2. As linhas de código que podem ser convertidas ficam **destacadas** no editor:
     - 🟢 **Verde** = Elementos de texto
     - 🟠 **Laranja** = Códigos de barras
  3. Dê **duplo clique** em uma linha destacada
  4. O elemento se transforma em um **mini-objeto arrastável** no canvas
  5. Arraste para reposicionar
  6. Clique em **"Atualizar Preview"** para aplicar a nova posição

> **💡 Dica:** Quando você converte uma linha, o preview principal regenera automaticamente SEM aquele elemento (chamamos isso de "pulo de corda"), e o elemento aparece como objeto independente que você pode mover livremente.

---

## 2. Editor de Código ZPL (Coluna Esquerda)

### Campo de Texto
- **O que é:** Editor de texto onde você escreve ou cola código ZPL
- **Funcionalidades:**
  - **Syntax Highlighting automático** — Comandos ZPL ficam coloridos:
    - Vermelho escuro (`^FO`, `^A0`, `^BY`) = Comandos
    - Verde azulado (números, parâmetros) = Parâmetros
  - **Auto-complete de `^XA`/`^XZ`** — Se o código não tiver, são adicionados automaticamente ao clicar em "Atualizar Preview"
  - **Colar inteligente** — Ao colar código, o syntax highlighting é reaplicado

---

## 3. Configurações da Etiqueta

Abaixo do editor, dentro do grupo "Configurações da Etiqueta":

### DPI
- **Opções:** 203 ou 300
- **O que faz:** Define a resolução da impressora
  - `203 DPI` = 8 dots por mm (impressoras mais antigas)
  - `300 DPI` = 12 dots por mm (padrão moderno)

### Unidade
- **Opções:** mm, cm, inches
- **O que faz:** Define a unidade de medida para largura e altura da etiqueta

### Largura
- **O que faz:** Define a largura da etiqueta (na unidade selecionada)
- **Padrão:** 54 mm

### Altura
- **O que faz:** Define a altura da etiqueta (na unidade selecionada)
- **Padrão:** 38 mm

### Botão "Atualizar Preview"
- **O que faz:** Envia o código ZPL para a API Labelary e exibe a imagem renderizada no canvas
- **Importante:**
  - Adiciona `^XA`/`^XZ` automaticamente se faltando
  - Regenera o preview excluindo elementos convertidos em mini-objetos
  - Mescla a posição dos mini-objetos de volta ao código ZPL
  - Tem debounce de 1.5 segundos para evitar erro 429

---

## 4. Canvas de Preview (Coluna Direita)

### Área de Visualização
- **O que é:** Canvas onde a etiqueta renderizada é exibida
- **Funcionalidades:**
  - Exibe a imagem da etiqueta gerada pela API Labelary
  - Mostra mini-objetos arrastáveis sobre a imagem
  - Grade de alinhamento (quando ativada)

### Interações no Canvas
- **Clique simples:** Coloca um novo elemento (se ferramenta ativa)
- **Duplo clique em mini-objeto:** Abre modal de edição
- **Arrastar mini-objeto:** Move o elemento
- **Ctrl + Scroll:** Zoom (10% a 400%)

---

## 5. Controles Abaixo do Preview

### Grupo "Movimento"
- **Travar X:** Impede movimento horizontal dos elementos
- **Travar Y:** Impede movimento vertical dos elementos

### Grupo "Grade"
- **Exibir:** Mostra/oculta a grade no canvas
- **Alinhar (Snap):** Faz elementos encaixarem nos pontos da grade ao serem soltos
- **Espaço:** Define o espaçamento da grade (10, 50, 100 ou 1000 pixels)

### Indicador de Resolução
- Canto inferior direito
- Mostra as dimensões atuais da janela (ex: `1400x700`)
- Atualiza em tempo real ao redimensionar

---

## 6. Menu Configurações > Preferências

Abre um modal com as seguintes opções:

### Tema
- **Padrão** — Fundo claro, textos escuros
- **Escuro Laranja** — Fundo escuro com detalhes em laranja
- **Escuro Dourado** — Fundo escuro com detalhes dourados
- **Cinza** — Fundo cinza claro com tons azulados

### Fontes
- **Fonte do Editor ZPL:** Família (Consolas, Courier New, etc.) e tamanho
- **Fonte da Interface:** Família (Segoe UI, Arial, etc.) e tamanho

### Tamanho do Canvas
- **Largura e Altura máximas** (em pixels)

### Tamanho Inicial da Janela
- **Largura e Altura** da janela ao abrir o programa

---

## 7. Modais de Edição

### Editar Texto (duplo clique em texto)
- **Texto:** Conteúdo do `^FD`
- **Posição X/Y:** Coordenadas do `^FO`
- **Altura/Largura:** Parâmetros da fonte `^A0`

### Editar Código de Barras (duplo clique em barcode)
- **Dados:** Conteúdo do `^FD` (números do código de barras)
- **Posição X/Y:** Coordenadas do `^FO`
- **Altura:** Altura das barras

---

## 8. Atalhos

| Atalho | Ação |
|--------|------|
| `Ctrl + Scroll` | Zoom no canvas |
| `Duplo clique` (editor, modo Conv.) | Converter linha em mini-objeto |
| `Duplo clique` (canvas) | Editar mini-objeto |
| `Arrastar` | Mover mini-objeto |

---

*Autor: Tiago Marcondes Schadeck — Março 2026*
