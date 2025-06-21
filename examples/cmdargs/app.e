class
    APPLICATION

inherit
    ARGUMENTS

create
    make
    
feature
                    
    make
    local
        i: INTEGER
    do
        print ("Переданные аргументы:%N")

        from
            i := 1
        until
            i > argument_count
        loop
            print (argument (i) + "%N")
            i := i + 1
        end
    end
end
