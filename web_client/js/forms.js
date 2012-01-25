Array.prototype.max = function() {
var max = this[0];
var len = this.length;
for (var i = 1; i < len; i++) if (this[i] > max) max = this[i];
return max;
}
Array.prototype.min = function() {
var min = this[0];
var len = this.length;
for (var i = 1; i < len; i++) if (this[i] < min) min = this[i];
return min;
}

var SERVER_ADRESS = '' 
var call = function (method, params, callback){
		    var query = JSON.stringify({			// It's JSON RPC
			    "method" : method,
			    "params" : params,
		    });
		
		    var rpc_xhr = new XMLHttpRequest();		// Classic Ajax code
		    rpc_xhr.onreadystatechange = function () {
			    if (rpc_xhr.readyState == 4 && rpc_xhr.status == 200) {
				    callback(rpc_xhr.responseText);
			    }
		    }
		    rpc_xhr.open("POST", SERVER_ADRESS+"json", true);
		    rpc_xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
		    rpc_xhr.send(query);
		    console.log(query)
}
$( function () {
    //TODO CHECK SERVER ADRESS AUTOMATICLY 



getUrlVars = function()
{
    var vars = [], hash;
    var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
    for(var i = 0; i < hashes.length; i++)
    {
        hash = hashes[i].split('=');
        vars.push(hash[0]);
        vars[hash[0]] = hash[1];
    }
    return vars;
}

var print_results = function (data) {
    $("#c_c").focus() 
   data = JSON.parse(data)[0]
   if (data != undefined) {
       console.log(data)
       if (data['code'] == 'ok')
           ghost_print(data['message'], 'light');
       if (data['code'] == 'fail')
           ghost_print(data['message'], 'red');   
   }
}

ghost_print = function (what_to_say, style2) {
 end = ""
 $("#logo").qtip({ 
        content: {
           text: what_to_say + end,
           title : {
            text : 'notification',
            button : true
           }
        },
        position: {
           type :"fixed",
           my: 'left center', // Use the corner...
           target : [90,50]
        },
        show: {
           event: false, // Don't specify a show event...
           ready: true // ... but show the tooltip when ready
        },
        hide: false,
        style: {
           classes: 'fixed ui-tooltip-shadow ui-tooltip-' + style2
        }
    });
}

update_list_campaigns = function() {
    $("#list_projects_campaigns").empty()
    list_campaigns = {};
    call("list_all_campaigns",new Array(), function (data) {
        list_campaigns = JSON.parse(data)[0]
        for (var i=0; i<list_campaigns.length;i++) {
            project = list_campaigns[i] 
            var html = "<li class='project unnested'><span class='title'>"
            html += project[0]+"</span> ("+project[1].length+")  <a href='"+project[0]+"' class='del-project' title='delete this project'><img src='images/bin.png' style='width:14px;'/></a> <ul style='display:none'>"
            for (var j=0; j<project[1].length;j++) {
                html += "<li>"
                
                if (project[1][j].status == 'finished')
                    html += '<img title="'+project[1][j].status+'" style="margin-left:20px; margin-top:5px;" src="images/green-dot.png" />'
                else
                    html += '<img title="'+project[1][j].status+'" style="margin-left:20px; margin-top:5px;" src="images/red-dot.png" />'
                html += "<span class='title_project'>" + project[1][j].name + "</span>"
                html += "<a href='"+project[0]+"' class='del-campaign' title='delete this campaign'><img  src='images/bin.png' style='margin-left:0.5em; width:14px;'/></a>"
                html+="</li>"
            }
            html += "</ul></li>"
            $("#list_projects_campaigns").append(html)
        }
    });
    
}


update_infos_campaign = function(e) {

    if (window.project && window.campaign) {
        if (window.refreshInfos) clearInterval(refreshInfos);
        $("#list_projects_campaigns .project .selected").toggleClass("selected")
        $(this).toggleClass("selected")
        project  = $(this).parent().parent().parent().children(".title").text()
        campaign = $(this).text()
        console.log(project, "/", campaign)
        update_infos_campaign_interval(project,campaign);
        if ( window.campaign != "*" )  {
            refreshInfos = setInterval(function () { console.log("updated"); update_infos_campaign_interval(project, campaign); }, 5000)
            console.log(window.campaign)
        }
        else {
            console.log("salut")
            clearInterval(refreshInfos);
        }
     }
}

update_infos_campaign_interval = function (project, campaign) {
    call("monitor",new Array(project,campaign),function(data) {
        data = JSON.parse(data)[0]
        campaign_data = data['message']['campaign']
        $("#infos_campaign .campaign_name").text(campaign_data['name'] )
        $("#i_date").text(campaign_data['date'])
        $("#i_download_delay").text(campaign_data['download_delay'])
        $("#i_depth").text(campaign_data['depth'])
        $("#i_status").text(campaign_data['status'])
        $("#i_nb_items").text(data['message']['nb_items'])
        if ( campaign_data['status'] == "alive" ) {
            $("#i_nb_items").append("&nbsp<img src='images/ajax-loader.gif'>")
        }
        $("#i_nb_duplicates").text(data['message']['nb_super'])
        $("#check_duplicates").attr("href", "?page=duplicates&project="+project+"&campaign="+campaign)
        $("#cancel_campaign").click(function() { cancel_campaign(); });
        start_urls = ""
        for (var i=0; i<campaign_data['start_urls'].length; i++) {
            url = campaign_data['start_urls'][i]
            start_urls += "<a href='" + url + "'>"+url+"</a>\n"
        }
        $("#start_urls").html(start_urls)
        html = "<table>"
        for (var i=0; i<data['message']['last_items'].length; i++) {
            html+="<tr><td>"+data['message']['last_items'][i]['depths'].min()+"</td><td>" + data['message']['last_items'][i]['title'] + "</td></tr>"
        }
        html+= "</table>"
        $("#last_items").html(html)
        $("#please_select").hide()
        $("#infos_project").hide()
        $("#infos_campaign").show()
    })
}

    
update_infos_project =  function () {
    project = $(this).text()
    campaign = "*"
    console.log(project)
    call("monitor_project",new Array(project),function(data) {
        data = JSON.parse(data)[0]
        console.log(data)
        $("#please_select").hide()
        $("#infos_campaign").hide()
        $("#i_nb_campaigns").text(data['nb_campaigns'])
        $("#i_total_number_items").text(data['nb_items'])
        $("#infos_project").show()
    });
}

update_list_project = function () {        
        call("list_project",new Array(), function (data) {
            $(".list_projects option").remove(); 
            window.list_projects = JSON.parse(data)[0];
            for (var i=0; i<window.list_projects.length; i++) {
                $(".list_projects").append("<option value='" +window.list_projects[i] + "'>" +window.list_projects[i] + "</option>")
            }
            update_list_campaigns();    
        })   
}

cancel_campaign = function () {   
        console.log("cancel_campaign", project, campaign);     
        call("cancel_campaign",new Array(project, campaign), function (data) {
            console.log(data)   
        })   
}

    
    $('#list_projects_campaigns .del-project').live('click', function(e) {
        e.preventDefault();
        project_name = $(this).attr("href")
        if (confirm("Delete this project ?"))
            call("remove_project",new Array(project_name),print_results)
        update_list_project()
    })
    
    $('#list_projects_campaigns .del-campaign').live('click', function(e) {
        e.preventDefault();
        var project = $(this).attr("href")
        var campaign = $(this).parent().text()
        if (confirm("Delete this campaign ?"))
            call("remove_campaign",new Array(project,campaign),print_results)
        console.log(project,campaign)
        update_list_project()
    })        

 

    
    $('#last_items_switch').click(function (e) {
        e.preventDefault();
        console.log($("#last_items"))
        $("#last_items").slideToggle(500);
    });
    $('#start_urls_switch').click(function (e) {
        e.preventDefault();
        $("#start_urls").slideToggle(500);
    });

    
    $('li.project .title').live('click', update_infos_project)
    $('#list_projects_campaigns .project li .title_project').live('click', update_infos_campaign)
    
    
    $('#list_projects_campaigns .project .title').live('click', function(e) {
        $(this).parent().children('ul').toggle()
        $(this).parent().toggleClass("nested")
        $(this).parent().toggleClass("unnested")
    })
    

    update_list_project()

    $("input:radio[name=c_search_type]").change(function () {
        if ( $("input:radio[name=c_search_type]:checked").val() == "words" || $("input:radio[name=c_search_type]:checked").val() == "titles" ) 
            $("tr#row_c_exact").show()
        else
            $("tr#row_c_exact").hide()
    });

    $("#campaign_form").bind('submit', function (e) { 
        e.preventDefault();
        if ($("#campaign_form").valid()) {
           // jsonrpc_startproject(project, campaign, start_urls, download_delay=30, depth=1):
            var project        = $("#c_p").val() ,
                campaign       = $("#c_c").val() ,
                start_titles     = $("#c_t").val().split("\n"),
                
                depth          = $("#c_d").val() ,
                search_type    = $("input:radio[name=c_search_type]:checked").val();
                download_delay = $("#c_dd").val();
                max_start_pages = $("#c_msp").val();
                max_cites_pages = $("#c_mcp").val();
                if ( $("#c_exact").attr("checked") ) exact = true
                else exact = false
            call("start_campaign",new Array(project,campaign, search_type, start_titles,download_delay,depth, max_start_pages, max_cites_pages, exact), print_results) 
        }    
    });
    $("#project_form").live("submit", function (e) { 
        e.preventDefault();
        if ($("#project_form").valid()) {
            var project_name = $("#p_p").val();
            call("start_project",new Array(project_name), function (data_sp) { 
                print_results(data_sp); 
                call("list_project",new Array(), function (data_lp) {
                    $("#c_p option").remove(); 
                    window.list_projects = JSON.parse(data_lp)[0];
                    for (var i=0; i<window.list_projects.length; i++) {
                        $("#c_p").append("<option value='" +window.list_projects[i] + "'>" +window.list_projects[i] + "</option>")
                    }
                    $("#c_p").val(project_name)
                    $dialog.dialog('close');  
                })   ;
            });
        }  
    });
    $("#export_gexf_form").submit(function (e) {
        ghost_print("You file is being generated, please wait...","light")
        e.preventDefault();
        var max_depth = $("#e_d").val();

        $dialog.dialog('close');  
        call("export_gexf",new Array(project, campaign, max_depth), function (data) {
            console.log(data)
            ghost_print("You can download the file <a href='downloader?file="+JSON.parse(data)[0]+"' title='Download GEXF'>here</a>", "light")

        }) 
    });
    
    $(".button_e_gexf").click(function (e) {
        $dialog.dialog('open'); 
    });
    
    $("#export_duplicates").click(function (e) {
        ghost_print("You file is being generated, please wait...","light")
        e.preventDefault();
        var max_depth = $("#e_d").val();

        $dialog.dialog('close');  
        call("export_duplicates",new Array(project, campaign), function (data) {
            console.log(data)
            ghost_print("You can download the file <a href='downloader?file="+JSON.parse(data)[0]+"' title='Download GEXF'>here</a>", "light")

        }) 
    });
    
    $("#button_e_json").bind('click', function (e) { 
        e.preventDefault();
           // jsonrpc_startproject(project, campaign, start_urls, download_delay=30, depth=1):
            call("export_json",new Array(project, campaign), function (data) {
                $("a").remove(":contains('Download Json')"); 
                ghost_print("Download the dump <a href='downloader?file="+JSON.parse(data)[0]+"' title='Download JSON'>Download Json</a>")
            })
             
    
    });
    $("#submit_e_zip").bind('click', function (e) { 
        e.preventDefault();
        if ($("#export_form").valid()) {
           // jsonrpc_startproject(project, campaign, start_urls, download_delay=30, depth=1):
            var project        = $("#e_p").val();
            call("export_zip",new Array(project), function (data) {
                $("a").remove(":contains('Download ZIP')");   
                $("#export_form fieldset").append("<a href='downloader?file="+JSON.parse(data)[0]+"' title='Download ZIP'>Download ZIP</a>")
            })
             
        }       
    });
    $("#update").bind('click', function (e) {
        update_list_project();
    });
    
    
    $("#add_project").click(function (e) {
        project_name = prompt("Please enter the name of the project you want to create");
        call("start_project",new Array(project_name), function (data_sp) {

            print_results(data_sp); 
            call("list_project",new Array(), function (data_lp) {
                $("#c_p option").remove(); 
                window.list_projects = JSON.parse(data_lp)[0];
                for (var i=0; i<window.list_projects.length; i++) {
                    $("#c_p").append("<option value='" +window.list_projects[i] + "'>" +window.list_projects[i] + "</option>")
                }
                $("#c_p").val(project_name)
                
            })   

        })      
    });
    
});
