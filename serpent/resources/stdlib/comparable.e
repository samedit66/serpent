deferred class
    COMPARABLE
-- Родитель для всех объектов, которые можно сравнить.
-- При наследовании необходимо реализовать два метода: is_less и is_equal,
-- остальные операторы сравнения имеют реализацию по умолчанию.

inherit
    ANY
    undefine
        is_equal
    end

feature
-- Операции сравнения.

    is_less (other: like Current): BOOLEAN
        -- Меньше ли этот объект чем other? 
        deferred
    end

    is_less_equal (other: like Current): BOOLEAN
        -- Меньше ли этот объект чем other или равен ему?
    then
        is_less (other) or else is_equal (other)
    end

    is_greater (other: like Current): BOOLEAN
        -- Больше ли этот объект чем other? 
    then
        not is_less (other) and then not is_equal (other)
    end

    is_greater_equal (other: like Current): BOOLEAN
        -- Больше ли этот объект чем other или равен ему?
    then
        is_greater (other) or is_equal (other)
    end

    max (other: like Current): like Current
    -- Возвращает больший объект между собой и `other`.
    do
        if Current >= other then
            Result := Current
        else
            Result := other
        end
    end

    min (other: like Current): like Current
    -- Возвращает больший объект между собой и `other`.
    do
        if Current <= other then
            Result := Current
        else
            Result := other
        end
    end

    in_range (lower, upper: like Current): BOOLEAN
    -- Находится ли текущий объект в пределах от `lower` до `upper`?
    then
        Current >= lower and then Current <= upper
    end

    compare, three_way_comparison (other: like Current): INTEGER
    -- Если текущий объект равен `other`, возвращается 0.
    -- Если текущий объект меньше `other`, возвращается -1.
    -- Если текущий объект больше `other`, возвращается 1.
    do
        if Current < other then
            Result := -1
        elseif Current > other then
            Result := 1
        end
    end
    
end
