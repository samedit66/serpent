class
    BOOLEAN
-- Булевский тип данных. Фактически является оберткой над int в Java.

inherit
    COMPARABLE
    STRINGABLE

feature
-- Операции сравнения.

    is_less (other: like Current): BOOLEAN
        external "Java"
        alias "com.eiffel.PLATFORM.BOOLEAN_is_less"
    end

    is_equal (other: like Current): BOOLEAN
        external "Java"
        alias "com.eiffel.PLATFORM.BOOLEAN_is_equal"
    end

feature
-- Конвертация в другие типы.

    out, to_string: STRING
        external "Java"
        alias "com.eiffel.PLATFORM.BOOLEAN_to_string"
    end
end
