deferred class STRINGABLE
-- Родитель всех объектов, которы можно представить в виде строки `STRING`.
-- Чаще всего необходим для операций IO.

feature

    out, to_string: STRING
    -- Представляет объект в виде строки.
        deferred
    end
end
