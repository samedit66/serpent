# serpent
serpent — это компилятор подмножества языка программирования **Eiffel**, который позволяет компилировать код в Java-байткод и выполнять его на JVM.

## Основные возможности:

- **Интеграция с Java:**  
  Легко подключайте и используйте произвольный Java-код для расширения возможностей ваших приложений. 🔌☕

- **Мощное наследование:**  
  Поддержка как одиночного, так и множественного наследования для гибкого построения иерархий классов и переиспользования кода. 🏛️✨

- **Удобные массивы:**  
  Поддержка динамических массивов с элементами одного типа — просто, понятно и эффективно для работы с данными. 📊✅

- **Простой и интуитивный синтаксис:**  
  Определяйте классы, методы и управляющие конструкции легко и понятно, сосредотачиваясь на логике приложения. 📝👌

- **Богатый набор встроенных инструментов:**  
  Встроенные операции ввода/вывода, сортировки, поиска и многое другое для быстрого старта разработки. 🔍💡

## Установка
Компилятор состоит из двух частей - парсер, написанный на **C**, собираемый при помощи **gcc**, **flex** и **bison** (под Windows рекомендуется воспользоваться [MSYS2](https://www.msys2.org/) для установки требуемого ПО) и семантический анализатор с генератором кода, написаннные на **Python**. В первую очередь необходимо собрать парсер:
```bash
make
```
Далее необходимо установить serpent через pip как пакет Python:
```bash
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

inherit
    IO

feature

    make
    do
        println ("Hello, world!")
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
- `--javaversion (-j)` — Версия Java. По умолчанию: `8`.
- `--outputdir (-d)` — Папка для сборки (генерации class-файлов). По умолчанию: `classes`.

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

## 4. Создание JAR-файла

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
