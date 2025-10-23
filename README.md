[Русская версия](#russian-version) | [English version](#english-version)

![serpent](https://github.com/user-attachments/assets/f0c4bc96-cb53-44d0-94cf-329d10001765)

# Russian version

**serpent** — это компилятор подмножества языка программирования **Eiffel**, который позволяет компилировать код в Java-байткод и выполнять его на JVM.

## Основные возможности:

- **Интеграция с Java:**  
  Легко подключайте и используйте произвольный Java-код для расширения возможностей ваших приложений. 🔌☕

- **Мощное наследование:**  
  Поддержка как одиночного, так и множественного наследования для гибкого построения иерархий классов и переиспользования кода. 🏛️✨

- **Встроенны коллекции:**
  Стандартная библиотека содержит реализацию динамического массива и хэш-таблицы — просто, понятно и эффективно для работы с данными. 📊✅

- **Простой и интуитивный синтаксис:**  
  Определяйте классы, методы и управляющие конструкции легко и понятно, сосредотачиваясь на логике приложения. 📝👌

- **Богатый набор встроенных инструментов:**  
  Встроенные операции ввода/вывода, сортировки, поиска, веб-сервер и многое другое для быстрого старта разработки. 🔍💡

## Установка
Компилятор состоит из двух частей - парсер, написанный на **C**, собираемый при помощи **gcc**, **flex** и **bison** (под Windows рекомендуется воспользоваться [MSYS2](https://www.msys2.org/) для установки требуемого ПО) и семантический анализатор с генератором кода, написаннные на **Python**.

Далее необходимо установить serpent через pip как пакет Python:
```bash
git clone https://github.com/samedit66/serpent.git
cd serpent
pip install .
```

После установки доступна команда `serpent` в терминале.

## Использование
### 1️⃣ Инициализация нового проекта
Создаёт минимальный проект с файлом `app.e`:
```bash
serpent init
cd app
```

После выполнения в папке `app` появится файл `app.e`:
```eiffel
class
    APPLICATION

create
    make

feature

    make
    do
        print ("Hello, world!%N")
    end

end
```

### 2️⃣ Компиляция проекта
Компилируем код из текущей папки `app`:
```bash
serpent build
```
После этого в папке `classes/` появятся скомпилированные файлы `.class`.

### 3️⃣ Запуск программы
Выполняем скомпилированный байткод:
```bash
serpent run
Hello, Eiffel!
```

### 4️⃣ Создание JAR-файла
Создаём исполняемый `.jar`:
```bash
serpent jar
```
Файл `app.jar` будет сохранён в текущую папку. Полученный файл необходимо запускать командной:
```bash
java -noverify -jar app.jar
```
Компилятор не генерирует stack map frames, поэтому проверку на их наличие необходимо отключить.

## Описание команд

## 1. Инициализация проекта

Создаёт минимальный проект Eiffel.

**Команда:**

```bash
serpent init [name]
```

**Параметры:**

- `name` — Имя проекта. Если не указано, по умолчанию используется `app`.

---

## 2. Компиляция проекта

Компилирует проект Eiffel.

**Команда:**

```bash
serpent build [source]
```

**Параметры:**

- `source` — Папка с исходными файлами проекта. По умолчанию: текущая директория (`.`).

**Флаги:**

- `--mainclass (-m)` — Главный класс. По умолчанию: `APPLICATION`.
- `--mainroutine (-r)` — Главный (стартовый) метод. По умолчанию: `make`.
- `--javaversion (-j)` — Версия Java. По умолчанию: `11`.
- `--outputdir (-d)` — Папка для сборки (генерации class-файлов). По умолчанию: `classes`.
- `--no-verbose` — Выключает отображение прогресс-бара статуса компиляции.

---
## 3. Запуск скомпилированных классов

Запускает скомпилированные классы проекта.

**Команда:**

```bash
serpent run [classpath]
```

**Параметры:**

- `[classpath]` — Папка с класс-файлами. По умолчанию: `classes`.

**Флаги:**

- `--mainclass (-m)` — Главный класс. По умолчанию: `APPLICATION`.

---
## 4. Компиляция и исполнение проекта

Выполняет компиляцию проекта и запуск скомпилированных файлов.
Сокращение для следующей последовательности команд:
```bash
serpent build
serpent run
```

**Команда:**

```bash
serpent exec [source]
```

**Параметры:**

- `source` — Папка с исходными файлами проекта. По умолчанию: текущая директория (`.`).

**Флаги:**

- `--mainclass (-m)` — Главный класс. По умолчанию: `APPLICATION`.
- `--mainroutine (-r)` — Главный (стартовый) метод. По умолчанию: `make`.
- `--javaversion (-j)` — Версия Java. По умолчанию: `11`.
- `--outputdir (-d)` — Папка для сборки (генерации class-файлов). По умолчанию: `classes`.
- `--no-verbose` — Выключает отображение прогресс-бара статуса компиляции.

---

## 5. Создание JAR-файла

Создаёт JAR-файл из скомпилированных классов.

**Команда:**

```bash
serpent jar [classpath]
```

**Параметры:**

- `[classpath]` — Папка с класс-файлами. По умолчанию: `classes`.

**Флаги:**

- `--mainclass (-m)` — Главный класс. По умолчанию: `APPLICATION`.
- `--outputdir (-d)` — Папка для сохранения JAR-файла. По умолчанию: текущая директория (`.`).
- `--jarname (-n)` — Имя создаваемого JAR-файла. По умолчанию: `app.jar`.

**Запуск JAR-файлов:**

Генерируемые class-файлы не могут быть запущены без указания флага `-noverify`, т.к. `serpent` не генерирует stack map frames.

```bash
java -noverify -jar app.jar
```

---

# English version

**serpent** — is a compiler for a subset of the **Eiffel** programming language that compiles code to Java bytecode and runs it on the JVM.

## Key features

- **Java integration:**
  Easily call and use arbitrary Java code to extend your applications. 🔌☕

- **Powerful inheritance:**
  Supports both single and multiple inheritance for flexible class hierarchies and code reuse. 🏛️✨

- **Built-in collections:**
  The standard library contains implementations of a dynamic array and a hash table — simple, clear and efficient for working with data. 📊✅

- **Simple and intuitive syntax:**
  Define classes, methods and control structures easily and clearly, focusing on the application logic. 📝👌

- **Rich set of built-in tools:**
  Built-in I/O, sorting, searching, a web server and much more to get you started quickly. 🔍💡

## Installation

The compiler consists of two parts — a parser written in **C** which is built using **gcc**, **flex** and **bison** (on Windows it is recommended to use [MSYS2](https://www.msys2.org/) to install the required tools) and a semantic analyzer with a code generator written in **Python**.

Next, install **serpent** as a Python package with `pip`:

```bash
git clone https://github.com/samedit66/serpent.git
cd serpent
pip install .
```

After installation the `serpent` command becomes available in the terminal.

## Usage

### 1️⃣ Initialize a new project
Creates a minimal project with the file `app.e`:

```bash
serpent init
cd app
```

After running the command, the folder `app` will contain `app.e`:

```eiffel
class
    APPLICATION

create
    make

feature

    make
    do
        print ("Hello, world!%N")
    end

end
```

### 2️⃣ Build the project
Compile the code from the current `app` folder:

```bash
serpent build
```

After that, compiled `.class` files will appear in the `classes/` directory.

### 3️⃣ Run the program
Run the compiled bytecode:

```bash
serpent run
Hello, Eiffel!
```

### 4️⃣ Create an executable JAR
Create an executable `.jar`:

```bash
serpent jar
```

The file `app.jar` will be saved to the current folder. Run it with:

```bash
java -noverify -jar app.jar
```

The compiler does not generate stack map frames, so bytecode verification must be disabled with `-noverify`.

## Command reference

### 1. Initialize a project
Creates a minimal Eiffel project.

**Command:**

```bash
serpent init [name]
```

**Parameters:**

- `name` — Project name. If omitted, the default is `app`.

---

### 2. Build the project
Compiles the Eiffel project.

**Command:**

```bash
serpent build [source]
```

**Parameters:**

- `source` — Directory with the project's source files. Default: current directory (`.`).

**Flags:**

- `--mainclass (-m)` — Main class. Default: `APPLICATION`.
- `--mainroutine (-r)` — Main (entry) routine. Default: `make`.
- `--javaversion (-j)` — Java version. Default: `11`.
- `--outputdir (-d)` — Output directory for generated `.class` files. Default: `classes`.
- `--no-verbose` — Disables the compilation progress bar.

---

### 3. Run compiled classes
Runs compiled classes of the project.

**Command:**

```bash
serpent run [classpath]
```

**Parameters:**

- `[classpath]` — Directory with class files. Default: `classes`.

**Flags:**

- `--mainclass (-m)` — Main class. Default: `APPLICATION`.

---

### 4. Build and run (shortcut)
Compiles the project and then runs the compiled files. Equivalent to:

```bash
serpent build
serpent run
```

**Command:**

```bash
serpent exec [source]
```

**Parameters:**

- `source` — Directory with the project's source files. Default: current directory (`.`).

**Flags:**

- `--mainclass (-m)` — Main class. Default: `APPLICATION`.
- `--mainroutine (-r)` — Main routine. Default: `make`.
- `--javaversion (-j)` — Java version. Default: `11`.
- `--outputdir (-d)` — Output directory for generated `.class` files. Default: `classes`.
- `--no-verbose` — Disables the compilation progress bar.

---

### 5. Create a JAR file
Creates a JAR file from compiled classes.

**Command:**

```bash
serpent jar [classpath]
```

**Parameters:**

- `[classpath]` — Directory with class files. Default: `classes`.

**Flags:**

- `--mainclass (-m)` — Main class. Default: `APPLICATION`.
- `--outputdir (-d)` — Directory to save the JAR file. Default: current directory (`.`).
- `--jarname (-n)` — Name of the generated JAR. Default: `app.jar`.

**Running JAR files:**

Generated class files cannot be run without the `-noverify` flag because `serpent` does not generate stack map frames.

```bash
java -noverify -jar app.jar
```
