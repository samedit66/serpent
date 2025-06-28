deferred class
    TEXT_FILE
-- Интерфейс для любого текстового файла.

feature
-- Запись в файл.

    put (c: CHARACTER)
    -- Записывает символ в файл.
    -- Доступно для вызова, если был открыт не в режиме чтения.
    deferred
    end
    
feature
-- Чтение из файла.

    last_character: CHARACTER
    -- Последний считанный символ.
    deferred
    end

    read_character
    -- Считывает символ из файла.
    deferred
    end

end
