class
    APPLICATION
                    
inherit
    IO
                                 
feature
            
    make
    local
        arr: ARRAY [BASE]
        i: INTEGER
    do
        create arr.with_capacity (4, 1)
        arr[1] := create {BASE}.make
        arr[2] := create {DERIVED1}.make
        arr[3] := create {DERIVED2}.make
        arr[4] := create {DIAMOND}.make

        from
            i := arr.lower
        until
            i > arr.upper
        loop
            arr[i].print_origin
            i := i + 1
        end
    end
end

class
    BASE

inherit
    IO
    COMPARABLE

create
    make

feature
    make
        do
        end

    print_origin
        do
            println ("Called from BASE")
        end

    is_less (other: like Current): BOOLEAN then False end

    is_equal (other: like Current): BOOLEAN then False end
end

class
    DERIVED1

inherit
    IO
    BASE redefine make, print_origin end

create
    make

feature
    make
        do
        end

    print_origin
        do
            println ("Called from DERIVED1")
        end
end

class
    DERIVED2

inherit
    IO
    BASE redefine make, print_origin end

create
    make

feature
    make
    do
    end

    print_origin
    do
        println ("Called from DERIVED2")
    end
end

class
    DIAMOND

inherit
    IO
    DERIVED1
        redefine make, print_origin end
    DERIVED2
        redefine make, print_origin end

create
    make

feature
    make
        do
        end

    print_origin
            -- Выводит сообщение с учётом ромбовидной структуры.
        do
            println ("Called from DIAMOND (diamond inheritance)")
        end
end
