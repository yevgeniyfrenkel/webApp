def clusterwarning(color, score):
    output = " "

    if color >= 0:
        if color == 0:
            temp = " Social street"
        if color == 1:
            temp = " Construction"
        if color == 2:
            temp = " Traffic"
        if color == 3:
            temp = " Pet"
        output = "Warning: High" + temp + " noise"
        template = '<div id="content"> <p><b><span style="color:red" >%s </span><br>Location score = %d/100 <a href="#codeword">more info</a> </b>  </p></div>'\
                   % (output, score)
        return template

    else:
        template = '<div id="content"> Location score = %d/100 <a href="#codeword">more info</a> </b></p></div>' % (
        score)
        return template
