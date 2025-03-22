class
    ANY

create
    default_create

feature
-- Конструкторы.

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
-- Структурное сравнение объектов.
-- Изначально, предполагалось, что данные операции будут определены
-- внутри класса EQ, но в итоге было принято решение вынести их в ANY,
-- для обеспечения совместимости с EiffelStudio.

    is_equal (other: like Current): BOOLEAN
    -- Возвращает `True`, если объекты равны в структурном смысле,
    -- и `False` в противном случае. Реализация по умолчанию совпадание
    -- с ссылочным сравнением.
    then
        is_same (other)
    end

    is_not_equal (other: like Current): BOOLEAN
    -- Возвращает `True`, если объекты не равны в структуруном смысле,
    -- и `False` в противном случае.
    then
        not is_equal (other)
    end

feature
-- Ссылочное сравнение объектов.

    is_void (other: ANY): BOOLEAN
    -- Является ли объект `other` `Void`?
        external "Java"
        alias "com.eiffel.PLATFORM.ANY_is_void"
    end

    is_not_void (other: ANY): BOOLEAN
    -- Не является ли объект `other` `Void`?
    then
        not is_void (other)
    end

    is_same (other: like Current): BOOLEAN
    -- Возвращает `True`, если объекты идентичны, и `False` в противном случае.
        external "Java"
        alias "com.eiffel.PLATFORM.ANY_is_same"
    end

    is_not_same (other: like Current): BOOLEAN
    -- Возвращает `True`, если объекты не идентичны, и `False` в противном случае.
    then
        not is_same (other)
    end

feature {NONE}
-- Стандартный поток ввода/вывода.
    cached_io: IO

feature
-- Функции для работы со стандартным потоком ввода/вывода.
-- Определены для совместимости со стандартной реализацией EiffelStudio.

    io: IO
    -- Возвращает стандартный поток ввода/вывода.
    do
        if is_void (cached_io) then
            create cached_io
        end

        Result := cached_io
    end

    print (s: STRING)
    -- Печатает строку `s` в стандартный поток вывода.
    do
        io.put_string (s)
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
