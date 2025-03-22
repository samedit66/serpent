class
    APPLICATION

create
    make

feature
            
    make
    local
        arr: ARRAY [BASE]
        d1: DERIVED1
        d2: DERIVED2
        d: DIAMOND
        i: INTEGER
    do
        create arr.with_capacity (4, 1)

        arr[1] := create {BASE}

        create d1
        arr[2] := d1

        create d2
        arr[3] := d2

        create d
        arr[4] := d

        from
            i := arr.lower
        until
            i > arr.upper
        loop
            arr[i].print_origin
            io.new_line
            i := i + 1
        end
    end
end
