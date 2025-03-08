# serpent
serpent — это компилятор подмножества языка программирования **Eiffel**, который позволяет компилировать код в Java-байткод и выполнять его на JVM.

## Возможности
Serpent поддерживает базовые возможности **Eiffel**, включая:
- Определение классов и методов (`feature`)
- Основные управляющие конструкции (`if`, `loop`)
- Работа с примитивными типами (`INTEGER`, `BOOLEAN`, `STRING`)
- Вывод в консоль (`print`)

## Сборка из исходников
Для сборки парсера требуется **gcc**, **flex**, **bison**:
```bash
make
```
Для запуска тестов необходимо Python:
```bash
python -m venv venv
./venv/Scripts/activate
python -m pip install -r requirements_dev.txt
make test
```

## Установка через `pip`
Для удобного использования serpent можно установить как Python-пакет:
```bash
pip install -e .
```
После установки доступна команда `serpent` в терминале.

## Использование
### 1️⃣ Инициализация нового проекта
Создаёт минимальный проект с файлом `app.e`:
```powershell
PS C:\Projects> serpent init
PS C:\Projects> cd app
```

После выполнения в папке `app` появится файл `app.e`:
```eiffel
class APPLICATION
feature
    make
    do
        "Hello, Eiffel!".print
    end
end
```

### 2️⃣ Компиляция проекта
Компилируем код из текущей папки:
```powershell
PS C:\Projects\app> serpent build .
```
После этого в папке `output/` появятся скомпилированные файлы `.class`.

### 3️⃣ Запуск программы
Выполняем скомпилированный байткод:
```powershell
PS C:\Projects\app> serpent run
Hello, Eiffel!
```

### 4️⃣ Создание JAR-файла
Создаём исполняемый `.jar`:
```powershell
PS C:\Projects\app> serpent jar
```
Файл `application.jar` будет сохранён в `output/`.

## Дополнительные параметры команд
- `serpent build <папка>` — компиляция проекта (по умолчанию текущая папка)
- `serpent run <папка>` — запуск скомпилированных классов
- `serpent jar <папка>` — создание JAR-файла
- Флаги:
  - `--mainclass` (`-m`) — главный класс (`APPLICATION` по умолчанию)
  - `--mainroutine` (`-r`) — стартовый метод (`make` по умолчанию)
  - `--javaversion` (`-j`) — версия Java (по умолчанию 8)
  - `--build` (`-b`) — папка для сборки (`output` по умолчанию)
