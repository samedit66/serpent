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
-- Операции ввода/вывода

    print
        external "Java"
        alias "com.eiffel.PLATFORM.ANY_print"
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
