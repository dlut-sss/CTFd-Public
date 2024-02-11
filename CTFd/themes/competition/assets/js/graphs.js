import $ from "jquery";
import * as echarts from 'echarts';
import dayjs from "dayjs";
import 'dayjs/locale/zh-cn';
import 'dayjs/locale/en';
import {cumulativeSum, colorHash} from "./utils";

function getCookieForLanguage(name) {
    const cookies = document.cookie.split('; ');
    for (const cookie of cookies) {
        const [cookieName, cookieValue] = cookie.split('=');
        if (cookieName === name) {
            return decodeURIComponent(cookieValue);
        }
    }
    return "zh";
}

const graph_configs = {
    score_graph: {
        format: (type, id, name, _account_id, responses) => {
            let option = {
                textStyle: {
                    color: 'white'  // 将整个图表中的文字颜色设置为白色
                },
                title: {
                    left: "center",
                    text: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Score over Time" : "得分曲线"),
                    textStyle: {
                        color: 'white'
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
                    bottom: 0,
                    data: [name],
                    textStyle: {
                        color: 'white'
                    },
                },
                toolbox: {
                    feature: {
                        saveAsImage: {}
                    },
                    iconStyle: {
                        borderColor: "rgba(255, 255, 255, 1)",
                    },
                },
                grid: {
                    containLabel: true
                },
                xAxis: [
                    {
                        type: "category",
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

            const times = [];
            const scores = [];
            const solves = responses[0].data;
            const awards = responses[2].data;
            const total = solves.concat(awards);

            total.sort((a, b) => {
                return new Date(a.date) - new Date(b.date);
            });

            for (let i = 0; i < total.length; i++) {
                const date = dayjs(total[i].date);
                times.push(date.toDate());
                try {
                    scores.push(total[i].challenge.value);
                } catch (e) {
                    scores.push(total[i].value);
                }
            }

            times.forEach(time => {
                option.xAxis[0].data.push(time);
            });

            option.series.push({
                name: window.stats_data.name,
                type: "line",
                label: {
                    normal: {
                        show: true,
                        position: "top"
                    }
                },
                areaStyle: {
                    normal: {
                        color: colorHash(name + id)
                    }
                },
                itemStyle: {
                    normal: {
                        color: colorHash(name + id)
                    }
                },
                data: cumulativeSum(scores)
            });
            return option;
        }
    },

    category_breakdown: {
        format: (type, id, name, account_id, responses) => {
            let option = {
                textStyle: {
                    color: 'white'  // 将整个图表中的文字颜色设置为白色
                },
                title: {
                    left: "center",
                    text: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Category Breakdown" : "类别细分"),
                    textStyle: {
                        color: 'white'
                    },
                },
                tooltip: {
                    trigger: "item"
                },
                toolbox: {
                    show: true,
                    feature: {
                        saveAsImage: {}
                    },
                    iconStyle: {
                        borderColor: "rgba(255, 255, 255, 1)",
                    },
                },
                legend: {
                    type: "scroll",
                    orient: "vertical",
                    top: "middle",
                    right: 0,
                    data: [],
                    textStyle: {
                        color: 'white'
                    },
                },
                series: [
                    {
                        name: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Category Breakdown" : "类别细分"),
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
                                    formatter: function (data) {
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
                        labelLine: {
                            show: false
                        },
                        data: []
                    }
                ]
            };
            const solves = responses[0].data;
            const categories = [];

            for (let i = 0; i < solves.length; i++) {
                categories.push(solves[i].challenge.category);
            }

            const keys = categories.filter((elem, pos) => {
                return categories.indexOf(elem) == pos;
            });

            const counts = [];
            for (let i = 0; i < keys.length; i++) {
                let count = 0;
                for (let x = 0; x < categories.length; x++) {
                    if (categories[x] == keys[i]) {
                        count++;
                    }
                }
                counts.push(count);
            }

            keys.forEach((category, index) => {
                option.legend.data.push(category);
                option.series[0].data.push({
                    value: counts[index],
                    name: category,
                    itemStyle: {color: colorHash(category)}
                });
            });

            return option;
        }
    },

    solve_percentages: {
        format: (type, id, name, account_id, responses) => {
            const solves_count = responses[0].data.length;
            const fails_count = responses[1].meta.count;
            let option = {
                textStyle: {
                    color: 'white'  // 将整个图表中的文字颜色设置为白色
                },
                title: {
                    left: "center",
                    text: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Solve Percentages" : "解出比例"),
                    textStyle: {
                        color: 'white'
                    },
                },
                tooltip: {
                    trigger: "item"
                },
                toolbox: {
                    show: true,
                    feature: {
                        saveAsImage: {}
                    },
                    iconStyle: {
                        borderColor: "rgba(255, 255, 255, 1)",
                    },
                },
                legend: {
                    orient: "vertical",
                    top: "middle",
                    right: 0,
                    data: ["Fails", "Solves"],
                    textStyle: {
                        color: 'white'
                    },
                },
                series: [
                    {
                        name: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Solve Percentages" : "提交比例"),
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
                                    formatter: function (data) {
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
                                value: fails_count,
                                name: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Fails" : "错误提交"),
                                itemStyle: {color: "rgb(207, 38, 0)"}
                            },
                            {
                                value: solves_count,
                                name: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Solves" : "正确提交"),
                                itemStyle: {color: "rgb(0, 209, 64)"}
                            }
                        ]
                    }
                ]
            };

            return option;
        }
    }
};

export function createGraph(
    graph_type,
    target,
    data,
    type,
    id,
    name,
    account_id
) {
    const cfg = graph_configs[graph_type];

    let chart = echarts.init(document.querySelector(target),null,{locale:getCookieForLanguage("Scr1wCTFdLanguage")});
    chart.setOption(cfg.format(type, id, name, account_id, data));
    $(window).on("resize", function () {
        if (chart != null && chart != undefined) {
            chart.resize();
        }
    });
}

export function updateGraph(
    graph_type,
    target,
    data,
    type,
    id,
    name,
    account_id
) {
    const cfg = graph_configs[graph_type];

    let chart = echarts.init(document.querySelector(target),null,{locale:getCookieForLanguage("Scr1wCTFdLanguage")});
    chart.setOption(cfg.format(type, id, name, account_id, data));
}

export function disposeGraph(target) {
    echarts.dispose(document.querySelector(target));
}
