class INTEGER
feature
    plus (other: like Current): like Current
        external "Java"
        alias "com.eiffel.PLATFORM.INTEGER_plus"
    end

    is_equal (other: like Current): BOOLEAN
        external "Java"
        alias "com.eiffel.PLATFORM.INTEGER_is_equal"
    end
end
