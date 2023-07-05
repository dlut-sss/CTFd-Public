function updatescores() {
    $.get(script_root + '/scores', function (data) {
        teams = $.parseJSON(JSON.stringify(data));
        console.log(teams);
        $('#scoreboard > tbody').empty()
        for (var i = 0; i < teams.length; i++) {
            if (teams[i].userid !== "") {
                row = "<tr><td>{0}</td><td><a href='/users/{1}' title='{5}'>{2}</a><td>{3}</td></td><td>{4}</td>".format(i + 1, teams[i].userid, htmlentities(teams[i]['name']), teams[i].affiliation, teams[i].score, teams[i].username);
            }
            else {
                row = "<tr><td>{0}</td><td><a href='/teams/{1}' title='{5}'>{2}</a><td>{3}</td></td><td>{4}</td>".format(i + 1, teams[i].teamid, htmlentities(teams[i]['name']), teams[i].affiliation, teams[i].score, teams[i].username);
            }
            chalids = new Array();
            tops = new Array();
            for (var k = 0; k < teams[i].solves.length; k++) {
                var chalid = parseInt(teams[i].solves[k].split("-")[0]);
                var top = parseInt(teams[i].solves[k].split("-")[1]);
                chalids.splice(0, 0, chalid);
                tops.splice(0, 0, new Array(chalid, top));
            }
            console.log(tops);

            for (var j = 0; j < challenges.length; j++) {
                // 
                // console.log(typeof(challenges[j].id));
                // console.log(teams[i].solves[j]);

                // chalids.splice(0,0,chalid);
                // console.log(chalid.toString() + top.toString());
                // console.log(chalids);
                pos = chalids.indexOf(challenges[j].id)
                if (pos != -1) {
                    if (tops[pos][1] == 1) {
                        row += '<td class="chalmark" style="color:#2bbc8a;"><img src="/matrix/static/medal1.png"></td>';
                    }
                    else if (tops[pos][1] == 2) {
                        row += '<td class="chalmark" style="color:#2bbc8a;"><img src="/matrix/static/medal2.png"></td>';
                    }
                    else if (tops[pos][1] == 3) {
                        row += '<td class="chalmark" style="color:#2bbc8a;"><img src="/matrix/static/medal3.png"></td>';
                    }
                    if (tops[pos][1] == 4) {
                        row += '<td class="chalmark" style="color:#2bbc8a;"><img src=""></td>';
                    }
                    if (tops[pos][1] == 5) {
                        row += '<td class="chalmark" style="color:#2bbc8a;"><img src=""></td>';
                    }
                    else if (tops[pos][1] == 0) {
                        row += '<td class="chalmark" style="color:#2bbc8a;"><img src="/matrix/static/flag.png"></td>';
                    }
                } else {
                    row += '<td class="chalmark"></td>';
                }
            }
            row += '</tr>';
            $('#scoreboard > tbody').append(row)
        };
    });
}

function cumulativesum(arr) {
    var result = arr.concat();
    for (var i = 0; i < arr.length; i++) {
        result[i] = arr.slice(0, i + 1).reduce(function (p, i) { return p + i; });
    }
    return result
}

function UTCtoDate(utc) {
    var d = new Date(0)
    d.setUTCSeconds(utc)
    return d;
}

function update() {
    updatescores();
}

setInterval(update, 300000); // Update scores every 5 minutes


// update()
