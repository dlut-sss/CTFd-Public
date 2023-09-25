import "./main";
import $ from "jquery";
import CTFd from "../CTFd";
import echarts from "echarts/dist/echarts.common";
import echarts_en from "echarts/dist/echarts-en.common";
import dayjs from "dayjs"; import 'dayjs/locale/zh-cn';import 'dayjs/locale/en';
import { htmlEntities, cumulativeSum, colorHash } from "../utils";

const graph = $("#score-graph");
const table = $("#scoreboard tbody");

const updateScores = () => {
  CTFd.api.get_scoreboard_list().then(response => {
    const teams = response.data;
    table.empty();

    for (let i = 0; i < teams.length; i++) {
      const row = [
        "<tr>",
        '<th scope="row" class="text-center">',
        i + 1,
        "</th>",
        '<td><a href="{0}/teams/{1}">'.format(
          CTFd.config.urlRoot,
          teams[i].account_id
        ),
        htmlEntities(teams[i].name),
        "</a></td>",
        "<td>",
        teams[i].score,
        "</td>",
        "</tr>"
      ].join("");
      table.append(row);
    }
  });
};

function getCookieForLanguage(name) {
  const cookies = document.cookie.split('; ');
  for (const cookie of cookies) {
    const [cookieName, cookieValue] = cookie.split('=');
    if (cookieName === name) {
      return decodeURIComponent(cookieValue);
    }
  }
  return null;
}

const buildGraphData = () => {
  return CTFd.api.get_scoreboard_detail({ count: 10 }).then(response => {
    const places = response.data;

    const teams = Object.keys(places);
    if (teams.length === 0) {
      return false;
    }

    const option = {
      textStyle: {
        color: 'white'  // 将整个图表中的文字颜色设置为白色
      },
      title: {
        left: "center",
        text: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? ("Top 10 " + (CTFd.config.userMode === "teams" ? "Teams" : "Users")) : ("前十名" + (CTFd.config.userMode === "teams" ? "队伍" : "用户"))),
        textStyle: {
          color: 'white',
        },
      },
      tooltip: {
        trigger: "axis",
        axisPointer: {
          type: "cross"
        }
      },
      legend: {
        type: "scroll",
        orient: "horizontal",
        align: "left",
        bottom: 35,
        data: [],
        textStyle: {
          color: 'white'  // 将图例文本颜色设置为白色
        },
      },
      toolbox: {
        feature: {
          dataZoom: {
            yAxisIndex: "none"
          },
          saveAsImage: {}
        },
        iconStyle: {
          borderColor: "rgba(255, 255, 255, 1)",
        }
      },
      grid: {
        containLabel: true
      },
      xAxis: [
        {
          type: "time",
          boundaryGap: false,
          data: []
        }
      ],
      yAxis: [
        {
          type: "value"
        }
      ],
      dataZoom: [
        {
          id: "dataZoomX",
          type: "slider",
          xAxisIndex: [0],
          filterMode: "filter",
          height: 20,
          top: 35,
          fillerColor: "rgba(233, 236, 241, 0.6)",
          textStyle: {
            color: 'white',
          },
        }
      ],
      series: []
    };

    for (let i = 0; i < teams.length; i++) {
      const team_score = [];
      const times = [];
      for (let j = 0; j < places[teams[i]]["solves"].length; j++) {
        team_score.push(places[teams[i]]["solves"][j].value);
        const date = dayjs(places[teams[i]]["solves"][j].date);
        times.push(date.toDate());
      }

      const total_scores = cumulativeSum(team_score);
      var scores = times.map(function(e, i) {
        return [e, total_scores[i]];
      });

      option.legend.data.push(places[teams[i]]["name"]);

      const data = {
        name: places[teams[i]]["name"],
        type: "line",
        label: {
          normal: {
            position: "top"
          }
        },
        itemStyle: {
          normal: {
            color: colorHash(places[teams[i]]["name"] + places[teams[i]]["id"])
          }
        },
        data: scores
      };
      option.series.push(data);
    }

    return option;
  });
};

const createGraph = () => {
  buildGraphData().then(option => {
    if (option === false) {
      // Replace spinner
      graph.html(
        '<h3 class="opacity-50 text-center w-100 justify-content-center align-self-center">'+(getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "No solves yet" : "尚未解出题目")+'</h3>'
      );
      return;
    }

    graph.empty(); // Remove spinners

    let chart;
    if (getCookieForLanguage("Scr1wCTFdLanguage") === "en")
    {
      chart = echarts_en.init(document.querySelector("#score-graph"));
    }else
    {
      chart = echarts.init(document.querySelector("#score-graph"));
    }
    chart.setOption(option);

    $(window).on("resize", function() {
      if (chart != null && chart != undefined) {
        chart.resize();
      }
    });
  });
};

const updateGraph = () => {
  buildGraphData().then(option => {

    let chart;
    if (getCookieForLanguage("Scr1wCTFdLanguage") === "en")
    {
      chart = echarts_en.init(document.querySelector("#score-graph"));
    }else
    {
      chart = echarts.init(document.querySelector("#score-graph"));
    }
    chart.setOption(option);
  });
};

function update() {
  updateScores();
  updateGraph();
}

$(() => {
  setInterval(update, 300000); // Update scores every 5 minutes
  createGraph();
});

window.updateScoreboard = update;
