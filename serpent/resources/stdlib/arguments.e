class
    ARGUMENTS
-- Аргументы командной строки.

feature

    argument_count: INTEGER
    -- Количество аргументов командной строки.
        external "Java"
        alias "com.eiffel.PLATFORM.ARGUMENTS_argument_count"
    end

    argument (i: INTEGER): STRING
    -- Аргумент под индексом `i`:
    --   `i = 1` - первый аргумент,
    --   `i = 2` - второй аргумент и так далее...
        external "Java"
        alias "com.eiffel.PLATFORM.ARGUMENTS_argument"
    end

end
