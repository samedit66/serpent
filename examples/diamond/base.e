class
    BASE

feature

    print_origin
    do
        io.put_string ("Called from BASE")
        io.new_line
    end

    non_redefined_anywhere
    do
        io.put_string ("Defined in BASE, not redefined anywhere")
        io.new_line
    end

    redefined_by_DERIVED1
    do
        io.put_string ("Should be redefined by DERIVED1")
        io.new_line
    end

    redefined_by_DERIVED2
    do
        io.put_string ("Should be redefined by DERIVED2")
        io.new_line
    end

end
