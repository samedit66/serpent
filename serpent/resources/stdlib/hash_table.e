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

    Default_capacity: INTEGER = 17
    -- Размер хэш-таблицы по умолчанию.

feature

    make (a_capacity: INTEGER)
    -- Создает хэш-таблицу с заданным размером.
    -- @param size Начальный размер хэш-таблицы.
    do
        capacity := a_capacity
        create keys.with_capacity (capacity, 1)
        create values.with_capacity (capacity, 1)
        create occupied.make_filled (False, keys.lower, keys.upper)
    end

    empty
    -- Создает "пустую" хэш-таблицу.
    do
        make (Default_capacity)
    end

feature

    current_keys: like keys
    -- Ключи, записанные в хэш таблицу.
    local
        i, j: INTEGER
        ks: like keys
    do
        create ks.with_capacity (count, 1)

        from
            i := 1
            j := 1
        until
            i > keys.count
        loop
            if occupied [i] then
                ks [j] := keys [i]
                j := j + 1
            end

            i := i + 1
        end

        Result := ks
    end

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

    capacity: INTEGER
    -- Сколько всего может быть элементов в хэш-таблице.

    is_full: BOOLEAN
    -- Заполнена ли хэш-таблица полностью?
    then
        count = occupied.count
    end

    is_empty: BOOLEAN
    -- Пустая ли хэш-таблица?
    then
        count = 0
    end

feature
-- Получение элементов хэш-таблицы.

    at, item (k: K): V
    -- Получить элемент по ключу `k`.
    -- @param k Ключ.
    -- @return Значение по ключу.
    local
        i: INTEGER
    do
        i := index_of (k)
        require_that (i /= 0, "Key " + k.out + "is not present in the hash table")
        Result := values [i]
    end

feature
-- Помещение новых элементов в хэш-таблицу.

    put (v: like item; k: K)
    local
        i: INTEGER
    do
        if is_full then rehash end

        i := index_of (k)

        keys [i] := k
        values [i] := v
        occupied [i] := True
    end

feature
-- Проверки вхождения элементов.

    has_key (k: K): BOOLEAN
    -- Есть ли переданный ключ в массиве?
    local
        i: INTEGER
    do
        from
            i := keys.lower
        until
            (i > keys.upper) or else Result
        loop
            Result := occupied [i] and then keys [i] = k
            i := i + 1
        end
    end

    has_value (v: like item): BOOLEAN
    -- Есть ли переданное значение в массиве?
    local
        i: INTEGER
    do
        from
            i := values.lower
        until
            (i > values.upper) or else Result
        loop
            Result := occupied [i] and then values [i] = v
            i := i + 1
        end
    end

feature {NONE}
-- Реализация.

    index_of (k: K): INTEGER
    -- Внутренний индекс для элемента `k`.
    -- Определяется следующим образом:
    -- - Если внутренний массив заполнен, доступного индекса нет, результат - 0;
    -- - Если переданного ключа нет, его индекc, результат - `internal_index (k)`;
    -- - Иначе, перебираем внутренний массив до тех пор, пока не найден индекс для данного элемента.
    do
        if is_full then
            Result := 0
        elseif not has_key (k) then
            Result := internal_index (k)
        else
            from
                Result := internal_index (k)
            until
                occupied [Result] and then keys [Result] = k
            loop
                Result := Result + 1
            
                if Result > keys.upper then
                    Result := keys.lower
                end
            end
        end
    end

    internal_index (k: K): INTEGER
    -- Индекс во внутреннем хранилище.
    then
        k.hash_code \\ keys.count + 1  
    end

    rehash
    -- Выполняет "рехэш" хэш-таблицы:
    -- увеличивает емкость в 1.5 раза и копирует все элементы
    -- в новую область памяти.
    local
        l_capacity: INTEGER
        l_keys: ARRAY [K]
        l_values: ARRAY [V]
        l_occupied: ARRAY [BOOLEAN]
        i: INTEGER
    do
        l_capacity := (capacity * 15 // 10)
        create l_keys.with_capacity (l_capacity, 1)
        create l_values.with_capacity (l_capacity, 1)
        create l_occupied.make_filled (False, keys.lower, keys.upper)

        from
            i := keys.lower
        until
            i = keys.upper
        loop
            l_keys [i] := keys [i]
            l_values [i] := values [i]
            l_occupied [i] := occupied [i]
        end

        capacity := l_capacity
        keys := l_keys
        values := l_values
        occupied := l_occupied
    end

end