class
    BOOLEAN
-- Булевский тип данных. Фактически является оберткой над int в Java.

inherit
    ANY redefine out, is_equal end
    COMPARABLE redefine out end

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

    out: STRING
        external "Java"
        alias "com.eiffel.PLATFORM.BOOLEAN_to_string"
    end

end
