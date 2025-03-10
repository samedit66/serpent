class IO
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

end
