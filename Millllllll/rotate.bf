recupere une constante code sur trois octets et la divise par 2 (oui; c'est tout pour l'instant)

x1 x2 x3 cp1 cp2 mult 1 0 0 x1/sqrt2 x2/sqrt2 x3/sqrt2

,>,>,<<

copy x1 on cp1
[->>>+>+<<<<]>>>>[-<<<<+>>>>]
set 1 for carry check
>>+<<
multiply by sqrt2/2*256
<[->
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    [->+
        [>]>[>>>+<]
        <<<
    <]
    <
]
copy mult to x2/sqrt2
>>[->>>>>+<<<<<]


<<<<
copy x2 on cp1
[->>+>+<<<]>>>[-<<<+>>>]
set x3/sqrt2 to 1 for carry checks
>>>>>>>+<<<<<<<
multiply by sqrt2/2*256
<[->
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    [->+
        [>]>[>>>>+
            [>]>[<<+>>>>]<<<
        <<]
        <<<
    <]
    <
]
set x3/sqrt2 back to 0 (from 1)
>>>>>>>>-<<<<<<<<
copy mult to x2/sqrt2
>>[->>>>>>+<<<<<<]

<<<
[->+>+<<]>>[-<<+>>]
set 1 for carry checks
>>>>>>>>+<<<<<<<<
multiply by sqrt2/2*256

<[->
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    [->+
        [>]>[>>>>>+
            [>]>[<<+
                [>>]>>[<< <+> >> >>>>]<< << <<
            >> >>]<< <
        <<<]<<<
    <]
    <
]
discard mult
>>[-]

rappel :
x1 x2 x3 cp1 cp2 mult 1 0 0 x1/sqrt2 x2/sqrt2 x3/sqrt2 1 0 0 0 0

copy x1 on cp1
<<<<<
[->>>+>+<<<<]>>>>[-<<<<+>>>>]
multiply by sqrt2/2*256*256%256
<[->
    ++++
    [->+
        [>]>[>>>>+
            [>>]>>[<<<+>>> >>>>]<<<<<<
        <<]
        <<<
    <]
    <
]
add mult to x3/sqrt2
>>[->>>>>>+
    [>]>[<<+>>>>]<<<
<<<<<<]

<<<<
copy x2 on cp1
[->>+>+<<<]>>>[-<<<+>>>]
multiply by sqrt2/2*256*256%256
<[->
    ++++
    [->+
        [>]>[>>>>>+
            [>]>[<<+
                [>]>>[<<<+>>>>]<<<
            >>>>]<<<
        <<<]
        <<<
    <]
    <
]
discard mult
>>[-]

rappel :
x1 x2 x3 cp1 cp2 mult 1 0 0 x1/sqrt2 x2/sqrt2 x3/sqrt2 1 0 0 0 0

copy x1 on cp1
<<<<<
[->>>+>+<<<<]>>>>[-<<<<+>>>>]
multiply by sqrt2/2*256*256*256%256
<[->
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    [->+
        [>]>[
            carry to x3/sqrt2
            >>>>>+
            [>]>[
                carry to x2/sqrt2
                <<+
                [>]>>[<<<+>>>>]<<<
            >>>>]<<<
        <<<]
        <<<
    <]
    <
]
discard mult
>>[-]

put x on xout and yout
>>>>
 [->>>>>>>> +>>>>>>>>+<<<<<<<< <<<<<<<<]
>[->>>>>>>> +>>>>>>>>+<<<<<<<< <<<<<<<<]
>[->>>>>>>> +>>>>>>>>+<<<<<<<< <<<<<<<<]

<< <<<< <<<<<
,>,>,<<

y1 y2 y3 cp1 cp2 mult 1 0 0 x1/sqrt2 x2/sqrt2 x3/sqrt2 1 0 0 0 0 xout1 xout2 xout3 1 0 0 0 0 yout1 yout2 yout3 1 0 0 0 0

copy y1 on cp1
[->>>+>+<<<<]>>>>[-<<<<+>>>>]
multiply by sqrt2/2*256
<[->
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    [->+
        [>]>[>>>+<]
        <<<
    <]
    <
]
copy mult to y2/sqrt2
>>[->>>>>+<<<<<]


<<<<
copy y2 on cp1
[->>+>+<<<]>>>[-<<<+>>>]
set y3/sqrt2 to 1 for carry checks
>>>>>>>+ >-< <<<<<<<
multiply by sqrt2/2*256
<[->
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    [->+
        [>]>[>>>>+
            [>]>[<<+>>>>]<<<
        <<]
        <<<
    <]
    <
]
set y3/sqrt2 back to 0 (from 1)
>>>>>>>>-<<<<<<<<
copy mult to y2/sqrt2
>>[->>>>>>+<<<<<<]

<<<
[->+>+<<]>>[-<<+>>]
set 1 for carry checks
>>>>>>>>+<<<<<<<<
multiply by sqrt2/2*256
<[->
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    [->+
        [>]>[>>>>>+
            [>]>[<<+
                [>]>>[<<<+>>>>]<<<
            >>>>]<<<
        <<<]<<<
    <]
    <
]
discard mult
>>[-]


copy y1 on cp1
<<<<<
[->>>+>+<<<<]>>>>[-<<<<+>>>>]
multiply by sqrt2/2*256*256%256
<[->
    ++++
    [->+
        [>]>[>>>>+
            [>>]>>[<<<+>>> >>>>]<<<<<<
        <<]
        <<<
    <]
    <
]
add mult to y3/sqrt2
>>[->>>>>>+
    [>]>[<<+>>>>]<<<
<<<<<<]

<<<<
copy y2 on cp1
[->>+>+<<<]>>>[-<<<+>>>]
multiply by sqrt2/2*256*256%256
<[->
    ++++
    [->+
        [>]>[>>>>>+
            [>]>[<<+
                [>]>>[<<<+>>>>]<<<
            >>>>]<<<
        <<<]
        <<<
    <]
    <
]
discard mult
>>[-]

copy y1 on cp1
<<<<<
[->>>+>+<<<<]>>>>[-<<<<+>>>>]
multiply by sqrt2/2*256*256*256%256
<[->
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    [->+
        [>]>[>>>>>+
            [>]>[<<+
                [>]>>[<<<+>>>>]<<<
            >>>>]<<<
        <<<]
        <<<
    <]
    <
]
discard mult
>>[-]


Add y to xout and yout

>>>>
set 1s for carry checks
>>>>>>>> >>>+>>>>> >>>+<<< <<<<< <<< <<<<<<<<


y1 y2 y3 cp1 cp2 mult 1 0 0 x1/sqrt2 x2/sqrt2 x3/sqrt2 1 0 0 0 0 xout1 xout2 xout3 1 0 0 0 0 yout1 yout2 yout3 1 0 0 0 0

[->>>>>>>>->>>>>>>>+<<<<<<<< <<<<<<<<]
>

[->>>>>>>>
    [>>]>>[<< <-> >> >>>>]<<<< <<
    -
    >>>>>>>>
    +
    [>>]>>[<< <+> >> >>>>]<<<< <<
    <<<<<<<< <<<<<<<<]

>

[->>>>>>>>
    [>]>[< <
        [>>]>>[<< <-> >> >>>>]<<<< <<
        -
        > > >>>]<<<
    -
    >>>>>>>>
    +
    [>]>[< <
        +
        [>>]>>[<< <+> >> >>>>]<<<< <<
        > > >>>]<<<
    <<<<<<<< <<<<<<<<]

>>>>>>.>.>.>>>>>>.>.>.
