deferred class
    COMPARABLE
-- Родитель для всех объектов, которые можно сравнить.
-- При наследовании необходимо реализовать два метода: is_less и is_equal,
-- остальные операторы сравнения имеют реализацию по умолчанию.

inherit
    EQ

feature
-- Операции сравнения.

    is_less (other: like Current): BOOLEAN
        -- Меньше ли этот объект чем other? 
        deferred
    end

    is_less_equal (other: like Current): BOOLEAN
        -- Меньше или этот объект чем other или равен ему?
    then
        is_less (other) or else is_equal (other)
    end

    is_greater (other: like Current): BOOLEAN
        -- Больше ли этот объект чем other? 
    then
        not is_less (other) and then not is_equal (other)
    end

    is_greater_equal (other: like Current): BOOLEAN
        -- Больше или этот объект чем other или равен ему?
    then
        is_greater (other) or is_equal (other)
    end
end
