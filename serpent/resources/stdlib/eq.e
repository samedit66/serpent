deferred class EQ

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
