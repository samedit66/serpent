class STRING
feature
    concat, plus (other: STRING): STRING
        external "Java"
        alias "com.eiffel.PLATFORM.STRING_concat"
    end

    count: INTEGER
        external "Java"
        alias "com.eiffel.PLATFORM.STRING_count"
    end
end
