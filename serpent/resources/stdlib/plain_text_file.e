class
    PLAIN_TEXT_FILE
-- Текстовый файл.

inherit
    TEXT_FILE

create
    make_open_read,
    make_open_write,
    make_open_append

feature

    make_open_read (fn: STRING)
    -- Открывает файл по имени для чтения.
    do
        is_open_read := open_read_mode (fn)
    end

    make_open_write (fn: STRING)
    -- Открывает файл по имени для записи.
    do
        is_open_write := open_write_mode (fn)
    end

    make_open_append (fn: STRING)
    -- Открывает файл по имени для добавления.
    do
        is_open_append := open_append_mode (fn)
    end

feature
-- Характеристики файла.

    is_open_read: BOOLEAN
    -- Получилось ли открыть файл для чтения?

    is_open_write: BOOLEAN
    -- Получилось ли открыть файл для записи?

    is_open_append: BOOLEAN
    -- Получилось ли открыть файл для добавления?

    exists: BOOLEAN
    -- Существует ли файл по заданному пути?
        external "Java"
        alias "com.eiffel.PLATFORM.PLAIN_TEXT_FILE_exists"
    end

    exhausted: BOOLEAN
    -- Остались ли в файле еще символы для чтения?
    -- Допустимо для вызова, если файл был открыт в режиме чтения.
    then
        is_void (last_character)
    end

feature
-- Освобождение ресурсов.

    close
    -- Закрывает файл.
        external "Java"
        alias "com.eiffel.PLATFORM.PLAIN_TEXT_FILE_close"
    end

feature
-- Запись в файл.

    put (c: CHARACTER)
    -- Записывает символ в файл.
    -- Доступно для вызова, если был открыт не в режиме чтения.
    do
        putc (c.code_point)
    end
    
feature
-- Чтение из файла.

    last_character: CHARACTER
    -- Последний считанный символ.

    read_character
    -- Считывает символ из файла.
    local
        code_point: INTEGER
    do
        code_point := getc

        if code_point /= -1 then
            last_character := code_point.to_character
        else
            last_character := Void
        end 
    end


feature {NONE}

    open_read_mode (fn: STRING): BOOLEAN
    -- Открывает файл по имени для записи.
        external "Java"
        alias "com.eiffel.PLATFORM.PLAIN_TEXT_FILE_make_open_read"
    end

    open_write_mode (fn: STRING): BOOLEAN
    -- Открывает файл по имени для записи.
        external "Java"
        alias "com.eiffel.PLATFORM.PLAIN_TEXT_FILE_make_open_write"
    end

    open_append_mode (fn: STRING): BOOLEAN
    -- Открывает файл по имени для добавления.
        external "Java"
        alias "com.eiffel.PLATFORM.PLAIN_TEXT_FILE_make_open_append"
    end

    getc: INTEGER
    -- Считывает символ из файла и возвращает его.
        external "Java"
        alias "com.eiffel.PLATFORM.PLAIN_TEXT_FILE_getc"
    end

    putc (code_point: INTEGER)
    -- Помещает символ в файл.
        external "Java"
        alias "com.eiffel.PLATFORM.PLAIN_TEXT_FILE_put"
    end

end
