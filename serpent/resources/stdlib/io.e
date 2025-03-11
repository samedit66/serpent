class
    IO
-- Класс для операций ввода/вывода с консолью.
-- Под капотом использует System.out и System.in.

feature
-- Операции вывода.

    new_line, put_new_line
    -- Помещает перевод строки в стандартный поток вывода.
    do
        put_string ("%N")
    end

    print (something: STRINGABLE)
    -- Печатает на экран что-то, что может быть представлено в виде строке.
    do
        put_string (something.to_string)
    end

    println (something: STRINGABLE)
    -- Печатает на экран что-то, что может быть представлено в виде строке.
    -- Дополнительно печатает символ перевода строки на экран.
    do
        print (something)
        new_line
    end

    put_string (s: STRING)
    -- Печатает строку в стандартный поток вывода (System.out).
        external "Java"
        alias "com.eiffel.PLATFORM.IO_put_string"
    end

feature
-- Поля, хранящие значение, считанные с потока ввода.

    last_string: STRING
    -- Последняя считанная через `read_line` строка.

    last_integer: INTEGER
    -- Последнее считанное через `read_integer` целое число.

    last_real: REAL
    -- Последнее считанное через `read_real` действительное число.

    last_character: CHARACTER
    -- Последний считанной через `read_character` символ.

feature
-- Операции вывода.

    read_line
    -- Выполняет считывание строки со стандартного ввода,
    -- записывая считанную строку в `last_string`.
    do
        last_string := input_string
    end

    read_integer
    -- Выполняет считывание целого числа со стандартного ввода,
    -- записывая считанную строку в `last_string`.
    do
        last_integer := input_integer
    end

    read_real
    -- Выполняет считывание действительного числа со стандартного ввода,
    -- записывая считанную строку в `last_string`.
    do
        last_real := input_real
    end

    read_character
    -- Выполняет считывание символа со стандартного ввода,
    -- записывая считанную строку в `last_string`.
    do
        last_character := input_character
    end

feature {NONE}

    input_string: STRING
    -- Считывает строку со стандартного ввода и возвращает её.
        external "Java"
        alias "com.eiffel.PLATFORM.IO_input_string"
    end

    input_integer: INTEGER
    -- Считывает целое число со стандартного ввода и возвращает его.
        external "Java"
        alias "com.eiffel.PLATFORM.IO_input_integer"
    end

    input_real: REAL
    -- Считывает действительное число со стандартного ввода и возвращает его.
        external "Java"
        alias "com.eiffel.PLATFORM.IO_input_real"
    end

    input_character: CHARACTER
    -- Считывает символ со стандартного ввода и возвращает его.
        external "Java"
        alias "com.eiffel.PLATFORM.IO_input_character"
    end
end
