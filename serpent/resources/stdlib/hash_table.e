class
    HASH_TABLE [K -> HASHABLE, V]
    -- Хэш-таблица, которая хранит пары ключ-значение.

create
    make,
    empty

feature {NONE}

    keys: ARRAY [K]
    -- Ключи.

    values: ARRAY [V]
    -- Значения.

    occupied: ARRAY [BOOLEAN]
    -- Какие ячейки являются занятыми.

feature

    make (size: INTEGER)
    -- Создает хэш-таблицу с заданным размером.
    -- @param size Начальный размер хэш-таблицы.
    do
        create keys.with_capacity (size, 1)
        create values.with_capacity (size, 1)
        create occupied.make_filled (False, keys.lower, keys.upper)
    end

feature

    count: INTEGER
    -- Возвращает количество пар ключ-значение в хэш-таблице.
    -- @return Количество пар ключ-значение в хэш-таблице.
    local
        i: INTEGER
    do
        from
            i := occupied.lower
        until
            i > occupied.upper
        loop
            if occupied [i] then Result := Result + 1 end
            i := i + 1
        end
    end

feature

    at, item (k: K): V
    -- Получить элемент по ключу `k`.
    -- @param k Ключ.
    -- @return Значение по ключу.
    do
    
    end

feature

    put (v: like item; k: K)
    do

    end

feature

    has_key (k: like item): BOOLEAN
    then
        index_of (k) /= 0
    end

    has_value (v: V): BOOLEAN
    local
        i: INTEGER
    do
        from
            i := values.lower
        until
            (i > values.upper) or else Result
        loop
            Result := values [i] = v
            i := i + 1
        end
    end

feature {NONE}

    index_of (k: like item): INTEGER
    local
        i: INTEGER
        seen_elements_count: INTEGER
    do
        seen_elements_count := 1
        Result := 0

        from
            i := internal_index (k)
        until
            (seen_elements_count = count) or else (keys [i] = k)
        loop
            i := i + 1
            seen_elements_count := seen_elements_count + 1
        end
    end

    internal_index (k: like item): INTEGER
    then
        k.hash_code % keys.count + 1  
    end

end