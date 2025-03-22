class ANY

create
    default_create

feature
-- Конструкторы

    default_create
    -- Конструктор по умолчанию.
    -- Вызывается в случае написания конструкции:
    --     create x и create {SOME_TYPE}
    -- Данные конструкции эквиваленты следующим:
    --     create x.default_create и create {SOME_TYPE}.default_create
    -- По умолчанию никаких действий не выполняет.
    do
    end

feature
-- Ссылочное сравнение объектов.

    is_void (other: ANY): BOOLEAN
    -- Является ли объект `Void`?
    external "Java"
    alias "com.eiffel.PLATFORM.ANY_is_void"
    end

feature {NONE}
-- Стандартный поток ввода/вывода.
    cached_io: IO

feature
-- Функции для работы со стандартным потоком ввода/вывода.

    io: IO
    -- Возвращает стандартный поток ввода/вывода.
    -- Определена для совместимости со стандартной реализацией Eiffel.
    do
        if is_void (cached_io) then
            create cached_io
        end

        Result := cached_io
    end

feature
-- Функции для работы со стандартным потоком ошибок.

    crash_with_message (message: STRING)
    -- Печатает сообщение об ошибке в System.err, после чего
    -- завершает работу приложения с кодом 1.
    external "Java"
    alias "com.eiffel.PLATFORM.ANY_crash_with_message"
    end
end
