deferred class
    EQ
-- Родитель для всех объектов, которые можно сранивать между собой.
-- Под сравнением подразумевается структурное равенство объектов.
-- При наследовании необходимо реализовать метод is_equal.
-- Остальные операторы сравнения имеют реализацию по умолчанию.

feature

    is_equal (other: like Current): BOOLEAN
        -- Равен ли этот объект другому other?
        deferred
    end

    is_not_equal (other: like Current): BOOLEAN
        -- Не равен ли этот объект другому other?
    then
        not is_equal (other)
    end
end
