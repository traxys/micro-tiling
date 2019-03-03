[

Prend un vecteur sous forme de 2 coordonnées de 3 octets chacunes en entrées
Renvoie le vecteur après une rotation d'un 8ieme de tour dans le sens trigonométrique sous le même format

Il est à noter que l'octet de poids fort est le premier
Si une valeur de sortie est négative alors le résultat est en complément à 2
Mais le résultat ne sera pas correct si le vecteur d'entree n'est pas dans le cadran des valeurs positives

Fonctionnement :

concept du brainfuck :
    le code brainfuck permet de controller un automate sur une bande d'octets
    le code est composé de 8 caractères tous les autres sont ignorés
    
    entrés/sorties (,.):
        la virgule permet de lire un charactère en entrée et le met dans la case mémoire sous l'automate
        le point permet de mettre l'octet de la case mémoire sur laquelle est l'automate en sortie

    déplacement (<>):
        les chevrons permettent de déplacer l'automate d'une case mémoire vers la gauche ou la droite
    
    opérations (+-):
        les opérateurs plus et moins permettent d'incrémenter ou décrémenter la case mémoire sur laquelle est l'automate de 1
        on notera que les opérateurs fonctionnent modulo 256 car chaque case mémoire est un seul octet
    
    controle ([]):
        les crochets sont une boucle "tant que la case mémoire sous l'automate est différente de 0"
        le test se déplace avec l'automate : ainsi une boucle ne contenant qu'un chevron fera se déplacer l'automate jusqu'à arriver sur une case nulle
    
    la bande de mémoire est initialisé à 0 au début du code
    c'est pour cela que cette zone de commentaire est entouré de crochets : rien n'y sera executé car on ne rentrera jamais dans cette 'boucle'

fonctionnement de la rotation :
    Vous aurez certainement noté que le brainfuck ne surpote pas les multiplications
    Mais une multiplication de deux octets modulo 256 n'est pas difficile à faire en utilisant une boucle :
        si la mémoire est initialisé comme ça :    x y 0 0
        [-> [->+>+<<] > [-<+>] < <]
        aprés execution de cette boucle la mémoire se retrouve comme ça : 0 y 0 x*y
        en décomposant la n'ieme exection de la boucle : (sont marqués de x la case mémoire sur laquelle est l'automate)
        [
            # x-n y 0 y*n
            # xxx
            ->
            
            # x-n-1 y 0 y*n
            #       x
            [->+>+<<]>
            
            # x-n-1 0 y y*(n+1)
            #         x

            [-<+>] < <
            # x-n-1 y 0 y*(n+1)
            # xxxxx
        ]
        Comme on termine et commence sur la premiere case mémoire la boucle continuera d'etre interprétée jusqu'a ce que la premiere case mémoire soit mise à 0
        vous aurez aussi pu noter que (comme la plupart des opérations simples en brainfuck) cette opération a détruit une partie des variables (ici seulement x)
    
    Mais toute la difficulté de ce programme vient du fait que l'on veut faire des multiplications sur plusieurs octets.
    Il faut donc être capable de transmettre les retenues.
    Pour cela, il suffit de tester ici V si la valeur de la variable de sortie est nulle et dans ce cas transmettre la retenue dans une autre variable.
                             [-> [->+>+ <<] > [-<+>] < <]
    On fait alors face à plusieurs problèmes :
        -le 'if' n'existe pas en brainfuck, il faut donc tout faire avec des boucles
        -on rentre dans la boucle dans le cas contraire de celui que l'on veut
        -il faut s'assurer que l'automate soit sur une case nulle pour sortir de la boucle (et que ca soit la même quelle que soit le résultat du test). Hors, un test destructif nécessiterait que l'on ait copié la variable avant, ce qui augmenterait la complexité du code
    La solution choisie est la suivante :
        mémoire initialement : x y 0 0 1 0 0 0
        (il faut bien penser à mettre un 1 sur la bonne case mémoire au préalable : [-]+)
        [-> [->+>+
            [>]>[>>>+<]<<<
        <<] > [-<+>] < <]
        et on obtient en mémoire : 0 y 0 x*y%256 1 0 0 x*y//256
    on remarquera que l'on a juste rajouté cette partie de gestion de retenue au code précédent :
        [>]>[>>>+<]<<<
        en notant T la position de l'automate si x*y%256 vaut 0, F sinon et A pour les deux:
            # x*y%256 1 0 0 carry
            # AAAAAAA
            [>]
            # x*y%256 1 0 0 carry
            # TTTTTTT   F
            >
            # x*y%256 1 0 0 carry
            #         T   F
            [>>>+<]
            # x*y%256 1 0 0 carry
            #             A
            # à cette étape on a ajouté 1 à la retenue si x*y%256 vallait 0
            <<<
            # x*y%256 1 0 0 carry
            # AAAAAAA
        Dans tous les cas on est revenu au point de départ
    Cette solution à l'avantage de ne pas détruire x*y%256 et d'etre rapide d'execution.
    Elle réaparaitra souvent dans le code ci-dessous avec différentes variantes dûes à des agencements de mémoire différents.
    

    La rotation d'un huitième de tour est particulièrement facile à effectuer car on remarque que cos(pi/4) = sin(pi/4) = sqrt(2)/2
    Ce qui veut dire que l'on n'a besoin de faire que deux multiplications par sqrt(2)/2
    la façon dont le calcul est fait ici est la suivante :
        on lit x en entrée (les 3 premiers octets)
        on multiplie x par sqrt(2)/2
        on le duplique dans les variables xout et yout
        on lit y en entrée (les 3 octets qui suivent)
        on multiplie y par sqrt(2)/2
        on le soustrait à xout et on l'ajoute à yout
        on écrit xout et yout en sortie

]


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
read y
,>,>,<<

y1 y2 y3 cp1 cp2 mult 1 0 0 y1/sqrt2 y2/sqrt2 y3/sqrt2 1 0 0 0 0 xout1 xout2 xout3 1 0 0 0 0 yout1 yout2 yout3 1 0 0 0 0

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


y1 y2 y3 cp1 cp2 mult 1 0 0 y1/sqrt2 y2/sqrt2 y3/sqrt2 1 0 0 0 0 xout1 xout2 xout3 1 0 0 0 0 yout1 yout2 yout3 1 0 0 0 0


add y to yout and subtract it to xout
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
        > > >>]<<<
    -
    >>>>>>>>
    +
    [>]>[< <
        +
        [>>]>>[<< <+> >> >>>>]<<<< <<
        > > >>]<<<
    <<<<<<<< <<<<<<<<]

>>>>>>.>.>.>>>>>>.>.>.
