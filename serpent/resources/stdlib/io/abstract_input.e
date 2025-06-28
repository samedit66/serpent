deferred class
    ABSTRACT_INPUT
-- Абстрактный ввод.

feature
-- Доступ к считанным элементам.

    last_character: CHARACTER
    -- Последний считанный символ.
    deferred
    end

    feature

    last_string: STRING
    -- Последняя считанная через `read_line` строка. Синоним для `last_line`.

    last_line: STRING
    -- Последняя считанная через `read_line` строка. Синоним для `last_string`.
    then last_string end

    last_integer: INTEGER
    -- Последнее считанное целое число.

    last_real: REAL
    -- Последнее считанное действительное число.

feature
-- Чтение.

    read_character
    -- Считывает символ из входного потока.
    local
        code_point: INTEGER
    do
        if is_not_void (buffer_character) then
            last_character := buffer_character
            buffer_character := Void
        else
            code_point := get_next_character

            if code_point /= -1 then
                last_character := code_point.to_character
            else
                last_character := Void
            end 
        end
    end

    read_line, read_string
    -- Считывает строку из входного потока.
    local
        buffer: STRING_BUFFER
    do
        create buffer.make

        from
            read_character
        until
            last_character = Void or else last_character = '%N'
        loop
            buffer.append_character (last_character)
            read_character
        end

        last_string := buffer.out
    end

    read_integer
    -- Считывает целое число из входного потока.
    local
        buffer: INTEGER
        is_negative: BOOLEAN
    do
        -- Пропускаем ведущие пробелы.
        from
            read_character
        until
            is_void (last_character)
            or else not last_character.is_space
        loop
            read_character
        end

        -- Определяем знак числа.
        if is_not_void (last_character) then
            is_negative := last_character = '-'
            if is_negative or else last_character = '+' then
                read_character
            end
        end

        -- Выполняем считывание всех числовых символов.
        from
        until
            is_void (last_character)
            or else not last_character.is_digit
        loop
            buffer := buffer * 10 + last_character.as_digit
            read_character
        end

        -- Помещаем последний символ обратно в поток ввода.
        if is_not_void (last_character) then
            put_back_last_character
        end

        if is_negative then
            buffer := -buffer
        end
        
        last_integer := buffer
    end

    read_real
        -- Считывает действительное число (с необязательной дробной частью и экспонентой).
    local
        buffer_sb: STRING_BUFFER
        s: STRING
    do
        -- 1) Пропускаем ведущие пробелы
        from
            read_character
        until
            is_void (last_character)
            or else not last_character.is_space
        loop
            read_character
        end

        -- 2) Готовим буфер для накопления символов числа
        create buffer_sb.make

        -- 3) Опциональный знак
        if not is_void (last_character) then
            if last_character = '-' or else last_character = '+' then
                buffer_sb.append_character (last_character)
                read_character
            end
        end

        -- 4) Целая часть
        from
        until
            is_void (last_character)
            or else not last_character.is_digit
        loop
            buffer_sb.append_character (last_character)
            read_character
        end

        -- 5) Дробная часть
        if not is_void (last_character) and then last_character = '.' then
            buffer_sb.append_character (last_character)
            read_character
            from
            until
                is_void (last_character)
                or else not last_character.is_digit
            loop
                buffer_sb.append_character (last_character)
                read_character
            end
        end

        -- 6) Экспоненциальная часть
        if not is_void (last_character) and then
           (last_character = 'E' or else last_character = 'e') then
            buffer_sb.append_character (last_character)
            read_character
            -- знак экспоненты
            if not is_void (last_character) and then
               (last_character = '+' or else last_character = '-') then
                buffer_sb.append_character (last_character)
                read_character
            end
            from
            until
                is_void (last_character)
                or else not last_character.is_digit
            loop
                buffer_sb.append_character (last_character)
                read_character
            end
        end

        -- 7) Пушбэк "лишнего" символа
        if not is_void (last_character) then
            put_back_last_character
        end

        -- 8) Конвертация в REAL
        s := buffer_sb.to_string
        -- Предполагаем, что метод STRING.to_real существует;
        -- в вашей платформе может быть to_real_64 или аналог.
        last_real := s.to_real
    end

feature {NONE}
-- Возврат символа обратно в поток.

    buffer_character: CHARACTER
    -- Возвращаенный обратно в поток ввода символ.

    put_back_last_character
    do
        require_that (
            is_void (buffer_character),
            "Cannot put more that one character back"
        )

        buffer_character := last_character
    end

feature {NONE}
-- Реализация.

    get_next_character: INTEGER
    -- Возвращает код следующего считанного символ из входного потока.
    -- @return Числовой следующего символа. `-1`, если символов не осталось.
    deferred
    end

end
