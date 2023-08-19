import "./main";
import "core/utils";
import CTFd from "core/CTFd";
import $ from "jquery";
import echarts from "echarts/dist/echarts-en.common";
import { colorHash } from "core/utils";

function language(en,zh) {
  const cookies = document.cookie.split('; ');
  for (const cookie of cookies) {
    const [cookieName, cookieValue] = cookie.split('=');
    if (cookieName === "Scr1wCTFdLanguage") {
      return (decodeURIComponent(cookieValue) === "en" ? en : zh);
    }
  }
  return zh;
}

const graph_configs = {
  "#solves-graph": {
    data: () => CTFd.api.get_challenge_solve_statistics(),
    format: response => {
      const data = response.data;
      const chals = [];
      const counts = [];
      const solves = {};
      for (let c = 0; c < data.length; c++) {
        solves[data[c]["id"]] = {
          name: data[c]["name"],
          solves: data[c]["solves"]
        };
      }

      const solves_order = Object.keys(solves).sort(function(a, b) {
        return solves[b].solves - solves[a].solves;
      });

      $.each(solves_order, function(key, value) {
        chals.push(solves[value].name);
        counts.push(solves[value].solves);
      });

      const option = {
        title: {
          left: "center",
          text: language("Solve Counts","解题总量")
        },
        tooltip: {
          trigger: "item"
        },
        toolbox: {
          show: true,
          feature: {
            mark: { show: true },
            dataView: { show: true, readOnly: false },
            magicType: { show: true, type: ["line", "bar"] },
            restore: { show: true },
            saveAsImage: { show: true }
          }
        },
        xAxis: {
          name: language("Solve Count","解题总量"),
          nameLocation: "middle",
          type: "value"
        },
        yAxis: {
          name: language("Challenge Name","题目名称"),
          nameLocation: "middle",
          nameGap: 60,
          type: "category",
          data: chals,
          axisLabel: {
            interval: 0,
            rotate: 0 //If the label names are too long you can manage this by rotating the label.
          }
        },
        dataZoom: [
          {
            show: false,
            start: 0,
            end: 100
          },
          {
            type: "inside",
            yAxisIndex: 0,
            show: true,
            width: 20
          },
          {
            fillerColor: "rgba(233, 236, 241, 0.4)",
            show: true,
            yAxisIndex: 0,
            width: 20
          }
        ],
        series: [
          {
            itemStyle: { normal: { color: "#1f76b4" } },
            data: counts,
            type: "bar"
          }
        ]
      };

      return option;
    }
  },

  "#keys-pie-graph": {
    data: () => CTFd.api.get_submission_property_counts({ column: "type" }),
    format: response => {
      const data = response.data;
      const solves = data["correct"];
      const fails = data["incorrect"];

      let option = {
        title: {
          left: "center",
          text: language("Submission Percentages","提交比例")
        },
        tooltip: {
          trigger: "item"
        },
        toolbox: {
          show: true,
          feature: {
            dataView: { show: true, readOnly: false },
            saveAsImage: {}
          }
        },
        legend: {
          orient: "vertical",
          top: "middle",
          right: 0,
          data: ["Fails", "Solves"]
        },
        series: [
          {
            name: language("Submission Percentages","提交比例"),
            type: "pie",
            radius: ["30%", "50%"],
            avoidLabelOverlap: false,
            label: {
              show: false,
              position: "center"
            },
            itemStyle: {
              normal: {
                label: {
                  show: true,
                  formatter: function(data) {
                    return `${data.name} - ${data.value} (${data.percent}%)`;
                  }
                },
                labelLine: {
                  show: true
                }
              },
              emphasis: {
                label: {
                  show: true,
                  position: "center",
                  textStyle: {
                    fontSize: "14",
                    fontWeight: "normal"
                  }
                }
              }
            },
            emphasis: {
              label: {
                show: true,
                fontSize: "30",
                fontWeight: "bold"
              }
            },
            labelLine: {
              show: false
            },
            data: [
              {
                value: fails,
                name: language("Fails","错误提交"),
                itemStyle: { color: "rgb(207, 38, 0)" }
              },
              {
                value: solves,
                name: language("Solves","正确提交"),
                itemStyle: { color: "rgb(0, 209, 64)" }
              }
            ]
          }
        ]
      };

      return option;
    }
  },

  "#categories-pie-graph": {
    data: () => CTFd.api.get_challenge_property_counts({ column: "category" }),
    format: response => {
      const data = response.data;

      const categories = [];
      const count = [];

      for (let category in data) {
        if (data.hasOwnProperty(category)) {
          categories.push(category);
          count.push(data[category]);
        }
      }

      for (let i = 0; i < data.length; i++) {
        categories.push(data[i].category);
        count.push(data[i].count);
      }

      let option = {
        title: {
          left: "center",
          text: language("Category Breakdown","类别细分")
        },
        tooltip: {
          trigger: "item"
        },
        toolbox: {
          show: true,
          feature: {
            dataView: { show: true, readOnly: false },
            saveAsImage: {}
          }
        },
        legend: {
          type: "scroll",
          orient: "vertical",
          top: "middle",
          right: 10,
          data: []
        },
        series: [
          {
            name: language("Category Breakdown","类别细分"),
            type: "pie",
            radius: ["30%", "50%"],
            label: {
              show: false,
              position: "center"
            },
            itemStyle: {
              normal: {
                label: {
                  show: true,
                  formatter: function(data) {
                    return `${data.percent}% (${data.value})`;
                  }
                },
                labelLine: {
                  show: true
                }
              },
              emphasis: {
                label: {
                  show: true,
                  position: "center",
                  textStyle: {
                    fontSize: "14",
                    fontWeight: "normal"
                  }
                }
              }
            },
            emphasis: {
              label: {
                show: true,
                fontSize: "30",
                fontWeight: "bold"
              }
            },
            data: []
          }
        ]
      };

      categories.forEach((category, index) => {
        option.legend.data.push(category);
        option.series[0].data.push({
          value: count[index],
          name: category,
          itemStyle: { color: colorHash(category) }
        });
      });

      return option;
    }
  },

  "#solve-percentages-graph": {
    layout: annotations => ({
      title: language("Solve Percentages per Challenge","每个题目的解出比例"),
      xaxis: {
        title: language("Challenge Name","题目名称")
      },
      yaxis: {
        title: (CTFd.config.userMode==="users"? language("Percentage of users (%)","解出的用户比例") : language("Percentage of teams (%)","解出的队伍比例")),
        range: [0, 100]
      },
      annotations: annotations
    }),
    data: () => CTFd.api.get_challenge_solve_percentages(),
    format: response => {
      const data = response.data;

      const names = [];
      const percents = [];

      const annotations = [];

      for (let key in data) {
        names.push(data[key].name);
        percents.push(data[key].percentage * 100);

        const result = {
          x: data[key].name,
          y: data[key].percentage * 100,
          text: Math.round(data[key].percentage * 100) + "%",
          xanchor: "center",
          yanchor: "bottom",
          showarrow: false
        };
        annotations.push(result);
      }

      const option = {
        title: {
          left: "center",
          text: language("Solve Percentages per Challenge","每个题目的解出比例")
        },
        tooltip: {
          trigger: "item",
          formatter: function(data) {
            return `${data.name} - ${(Math.round(data.value * 10) / 10).toFixed(
              1
            )}%`;
          }
        },
        toolbox: {
          show: true,
          feature: {
            mark: { show: true },
            dataView: { show: true, readOnly: false },
            magicType: { show: true, type: ["line", "bar"] },
            restore: { show: true },
            saveAsImage: { show: true }
          }
        },
        xAxis: {
          name: language("Challenge Name","题目名称"),
          nameGap: 40,
          nameLocation: "middle",
          type: "category",
          data: names,
          axisLabel: {
            interval: 0,
            rotate: 50
          }
        },
        yAxis: {
          name: (CTFd.config.userMode==="users"? language("Percentage of users (%)","解出的用户比例") : language("Percentage of teams (%)","解出的队伍比例")),
          nameGap: 50,
          nameLocation: "middle",
          type: "value",
          min: 0,
          max: 100
        },
        dataZoom: [
          {
            show: false,
            start: 0,
            end: 100
          },
          {
            type: "inside",
            show: true,
            start: 0,
            end: 100
          },
          {
            fillerColor: "rgba(233, 236, 241, 0.4)",
            show: true,
            right: 60,
            yAxisIndex: 0,
            width: 20
          },
          {
            type: "slider",
            fillerColor: "rgba(233, 236, 241, 0.4)",
            top: 35,
            height: 20,
            show: true,
            start: 0,
            end: 100
          }
        ],
        series: [
          {
            itemStyle: { normal: { color: "#1f76b4" } },
            data: percents,
            type: "bar"
          }
        ]
      };

      return option;
    }
  },

  "#score-distribution-graph": {
    layout: annotations => ({
      title: language("Score Distribution","得分分布"),
      xaxis: {
        title: language("Score Bracket","分数档次"),
        showticklabels: true,
        type: "category"
      },
      yaxis: {
        title: (CTFd.config.userMode==="users"? language("Number of users","用户数目") : language("Number of teams","队伍数目"))
      },
      annotations: annotations
    }),
    data: () =>
      CTFd.fetch("/api/v1/statistics/scores/distribution").then(function(
        response
      ) {
        return response.json();
      }),
    format: response => {
      const data = response.data.brackets;
      const keys = [];
      const brackets = [];
      const sizes = [];

      for (let key in data) {
        keys.push(parseInt(key));
      }
      keys.sort((a, b) => a - b);

      let start = "<0";
      keys.map(key => {
        brackets.push("{0} - {1}".format(start, key));
        sizes.push(data[key]);
        start = key;
      });

      const option = {
        title: {
          left: "center",
          text: language("Score Distribution","得分分布")
        },
        tooltip: {
          trigger: "item"
        },
        toolbox: {
          show: true,
          feature: {
            mark: { show: true },
            dataView: { show: true, readOnly: false },
            magicType: { show: true, type: ["line", "bar"] },
            restore: { show: true },
            saveAsImage: { show: true }
          }
        },
        xAxis: {
          name: language("Score Bracket","分数档次"),
          nameGap: 40,
          nameLocation: "middle",
          type: "category",
          data: brackets
        },
        yAxis: {
          name: (CTFd.config.userMode==="users"? language("Number of users","用户数目") : language("Number of teams","队伍数目")),
          nameGap: 50,
          nameLocation: "middle",
          type: "value"
        },
        dataZoom: [
          {
            show: false,
            start: 0,
            end: 100
          },
          {
            type: "inside",
            show: true,
            start: 0,
            end: 100
          },
          {
            fillerColor: "rgba(233, 236, 241, 0.4)",
            show: true,
            right: 60,
            yAxisIndex: 0,
            width: 20
          },
          {
            type: "slider",
            fillerColor: "rgba(233, 236, 241, 0.4)",
            top: 35,
            height: 20,
            show: true,
            start: 0,
            end: 100
          }
        ],
        series: [
          {
            itemStyle: { normal: { color: "#1f76b4" } },
            data: sizes,
            type: "bar"
          }
        ]
      };

      return option;
    }
  }
};

const createGraphs = () => {
  for (let key in graph_configs) {
    const cfg = graph_configs[key];

    const $elem = $(key);
    $elem.empty();

    let chart = echarts.init(document.querySelector(key));

    cfg
      .data()
      .then(cfg.format)
      .then(option => {
        chart.setOption(option);
        $(window).on("resize", function() {
          if (chart != null && chart != undefined) {
            chart.resize();
          }
        });
      });
  }
};

function updateGraphs() {
  for (let key in graph_configs) {
    const cfg = graph_configs[key];
    let chart = echarts.init(document.querySelector(key));
    cfg
      .data()
      .then(cfg.format)
      .then(option => {
        chart.setOption(option);
      });
  }
}

$(() => {
  createGraphs();
  setInterval(updateGraphs, 300000);
});
