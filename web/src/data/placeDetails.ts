export type PlaceDetailSummary = {
  title: string
  tags?: string[]
  price?: string
}

export type PlaceReview = {
  id: string
  name: string
  time: string
  text: string
  rating: number
  likes: number
  dislikes: number
  avatarBg: string
}

export type PlaceDetail = {
  title: string
  address: string
  hours: string
  status: string
  description: string
  price: string
  rating: string
  ratingCount: string
  heroWordmark: string
  heroCaption: string
  heroMarquee: string
  heroBackground: string
  reviews: PlaceReview[]
  reminders: string[]
  reminderNote: string
}

function makeReview(
  id: string,
  name: string,
  time: string,
  text: string,
  rating: number,
  avatarBg: string,
  likes = 513,
  dislikes = 8,
): PlaceReview {
  return { id, name, time, text, rating, likes, dislikes, avatarBg }
}

const placeDetailsByTitle: Record<string, PlaceDetail> = {
  'FILM电影时光书店': {
    title: 'FILM电影时光书店',
    address: '上海市徐汇区安福路322号',
    hours: '周一至周日9：00-19：00',
    status: '营业中',
    description:
      '坐落于上海市电影家协会大院内的老洋房中，是一家以电影、戏剧和艺术为主题的独立书店。庭院静谧幽雅，室内红木格调配合暗黄的光线，重现老上海电影制片厂的文学底蕴。提供咖啡、气泡水和电影主题的文创周边。',
    price: '人均 ¥43',
    rating: '4.8',
    ratingCount: '1252',
    heroWordmark: 'FILM',
    heroCaption: 'Books · Café',
    heroMarquee: '电影时光',
    heroBackground:
      'linear-gradient(180deg, rgba(28, 22, 18, 0.14) 0%, rgba(28, 22, 18, 0.48) 100%), radial-gradient(120% 90% at 50% 0%, rgba(255, 245, 219, 0.82) 0%, rgba(232, 211, 182, 0.86) 42%, rgba(143, 107, 76, 0.92) 100%), repeating-linear-gradient(130deg, rgba(255,255,255,0.1) 0 2px, rgba(0,0,0,0) 2px 16px)',
    reviews: [
      makeReview('film-1', '小优', '2 天前', '店内主题感强，适合拍照和短暂停留；但空间不算大，周日下午可能人多。', 5, '#e9d8cf'),
      makeReview('film-2', '杰克', '1 周前', '安福路宝藏电影书店！老洋房环境超有氛围感，店内循环播放老影片，满眼都是电影相关书籍，看书喝咖啡很惬意，影迷必逛。', 5, '#d9e4f5'),
      makeReview('film-3', '小艾', '1个月前', '专攻影视类书籍，选书专业，冷门画册、导演传记都能挖到。周末人多嘈杂，工作日来安安静静看书体验更佳。', 4, '#f0dfc8'),
    ],
    reminders: ['一个人阅读', '喜欢电影主题空间', '想轻松开启路线'],
    reminderNote: '周末下午可能作为紧张；若只想安安静静约等于，建议避开高峰时段。',
  },
  'RAC BAR（安福路店）': {
    title: 'RAC BAR（安福路店）',
    address: '上海市徐汇区安福路322弄1号',
    hours: '周一至周日 10:00-22:00',
    status: '营业中',
    description:
      '安福路街角的人气法式餐吧，白天适合露台小坐，傍晚氛围感更好。可点可颂、早午餐或一杯气泡酒，作为路线里的轻社交停留很合适。',
    price: '人均 ¥120-150',
    rating: '4.7',
    ratingCount: '986',
    heroWordmark: 'RAC BAR',
    heroCaption: 'Anfu Terrace',
    heroMarquee: '街角露台',
    heroBackground:
      'linear-gradient(180deg, rgba(21, 19, 17, 0.14) 0%, rgba(21, 19, 17, 0.52) 100%), radial-gradient(120% 110% at 20% 20%, rgba(255, 245, 228, 0.82) 0%, rgba(222, 196, 163, 0.85) 45%, rgba(118, 84, 61, 0.92) 100%)',
    reviews: [
      makeReview('rac-1', 'Yuki', '3 天前', '露台位置舒服，晴天拍照很好看，面包和咖啡都比较稳。', 5, '#efe3cf'),
      makeReview('rac-2', '阿哲', '6 天前', '周末排队明显，建议错峰来；如果只是想坐坐聊天，下午四点后体验更好。', 4, '#d7e5cf'),
    ],
    reminders: ['适合街角小坐', '适合两人聊天', '下午光线更好'],
    reminderNote: '热门时段需要等位，若你后面还想继续赶路线，建议把停留时间控制在 45 分钟左右。',
  },
  '一面春风（吴兴路总店/武康周边）': {
    title: '一面春风（吴兴路总店/武康周边）',
    address: '上海市徐汇区吴兴路277号附近',
    hours: '周一至周日 11:00-21:30',
    status: '营业中',
    description:
      '武康路附近口碑不错的小馆子，偏烟火气的本帮面食和热菜，适合作为路线尾声的一顿安稳晚餐，不需要太正式，也不会太匆忙。',
    price: '人均 ¥55-70',
    rating: '4.6',
    ratingCount: '735',
    heroWordmark: '一面春风',
    heroCaption: 'Wukang Supper',
    heroMarquee: '烟火本帮',
    heroBackground:
      'linear-gradient(180deg, rgba(28, 17, 13, 0.18) 0%, rgba(28, 17, 13, 0.58) 100%), radial-gradient(110% 100% at 24% 18%, rgba(255, 232, 210, 0.84) 0%, rgba(209, 144, 102, 0.88) 48%, rgba(96, 54, 35, 0.94) 100%)',
    reviews: [
      makeReview('ymcf-1', '泡泡', '4 天前', '面和浇头都很扎实，收尾来一顿很舒服，不会太油。', 5, '#ecd8bf'),
      makeReview('ymcf-2', '阿木', '2 周前', '门店不算大，但翻台快，晚饭点也没有想象中那么难等。', 4, '#d6e2f1'),
    ],
    reminders: ['适合路线收尾', '偏本帮风味', '建议晚餐前抵达'],
    reminderNote: '如果当天已经喝了咖啡或吃了甜品，这里更适合点一份热面或小份热菜，节奏会更舒服。',
  },
  '多抓鱼循环商店': {
    title: '多抓鱼循环商店',
    address: '上海市徐汇区安福路300号附近',
    hours: '周一至周日 10:30-20:30',
    status: '营业中',
    description:
      '集合二手书、服饰与循环生活方式的线下空间，逛起来很轻松，适合把路线的第一站切换成更有探索感的淘物体验。',
    price: '约 ¥60-70',
    rating: '4.7',
    ratingCount: '842',
    heroWordmark: '多抓鱼',
    heroCaption: 'Circular Store',
    heroMarquee: '循环商店',
    heroBackground:
      'linear-gradient(180deg, rgba(22, 24, 20, 0.14) 0%, rgba(22, 24, 20, 0.5) 100%), radial-gradient(100% 100% at 50% 0%, rgba(229, 244, 221, 0.88) 0%, rgba(173, 196, 140, 0.86) 44%, rgba(82, 107, 69, 0.94) 100%)',
    reviews: [
      makeReview('dzy-1', '暖暖', '5 天前', '二手书和衣服的状态都比预期好，慢慢逛很容易待久。', 5, '#d7ebcf'),
      makeReview('dzy-2', '东东', '1 周前', '选书偏年轻化，也有不少好玩的旧物件，适合一边逛一边拍。', 4, '#e7d9bf'),
    ],
    reminders: ['适合旧书淘选', '适合慢慢翻找', '容易超时停留'],
    reminderNote: '如果只是路线里短暂停留，建议先看服饰区或主题书架，不然很容易一逛就超过预留时间。',
  },
  '衡山和集': {
    title: '衡山和集',
    address: '上海市徐汇区衡山路880号',
    hours: '周一至周日 10:00-21:00',
    status: '营业中',
    description:
      '集书店、展陈、文创和活动空间于一体的复合文化场所，空间更完整，适合把第一站换成更正式的慢逛型目的地。',
    price: '约 ¥35-45',
    rating: '4.6',
    ratingCount: '1103',
    heroWordmark: '衡山和集',
    heroCaption: 'Books · Events',
    heroMarquee: '复合空间',
    heroBackground:
      'linear-gradient(180deg, rgba(15, 17, 28, 0.16) 0%, rgba(15, 17, 28, 0.56) 100%), radial-gradient(100% 100% at 20% 20%, rgba(226, 226, 248, 0.88) 0%, rgba(168, 169, 205, 0.86) 42%, rgba(68, 74, 120, 0.94) 100%)',
    reviews: [
      makeReview('hs-1', 'Luna', '2 天前', '空间大，展陈和书区连在一起，适合一个人慢慢逛。', 5, '#d8ddf2'),
      makeReview('hs-2', '阿宁', '9 天前', '活动比较多，偶尔会遇到局部区域更热闹，想安静看书可以往里面走。', 4, '#f1e0c6'),
    ],
    reminders: ['适合慢慢停留', '适合文化类路线', '骑行抵达更方便'],
    reminderNote: '如果你更看重安静感，建议避开活动开始前后的时间段，那时入口区域会明显更热闹。',
  },
  'MANNER COFFEE（安福路店）': {
    title: 'MANNER COFFEE（安福路店）',
    address: '上海市徐汇区安福路298号附近',
    hours: '周一至周日 7:30-20:30',
    status: '营业中',
    description:
      '更适合快速补一杯咖啡的街边店，出杯快、动线短，适合把第二站压缩成一个干净利落的短暂停留。',
    price: '约 ¥28-40',
    rating: '4.5',
    ratingCount: '903',
    heroWordmark: 'MANNER',
    heroCaption: 'Coffee',
    heroMarquee: '街角咖啡',
    heroBackground:
      'linear-gradient(180deg, rgba(24, 20, 17, 0.14) 0%, rgba(24, 20, 17, 0.54) 100%), radial-gradient(100% 100% at 28% 18%, rgba(246, 235, 225, 0.88) 0%, rgba(208, 184, 164, 0.84) 46%, rgba(105, 79, 61, 0.94) 100%)',
    reviews: [
      makeReview('manner-1', '橘子', '1 天前', '出杯很快，路过顺手买一杯很合适，适合路线里的过渡站。', 5, '#f2dcc8'),
      makeReview('manner-2', 'Peter', '1 周前', '店面不大，但效率高；如果只是想坐很久，就不如去更大的咖啡馆。', 4, '#dbe7f4'),
    ],
    reminders: ['适合快速补给', '站立或短坐', '工作日更顺畅'],
    reminderNote: '如果你想把路线留更多时间给后面的街区散步，这一站选它会更省时。',
  },
  'Café del Volcán': {
    title: 'Café del Volcán',
    address: '上海市徐汇区乌鲁木齐南路附近',
    hours: '周一至周日 10:00-21:00',
    status: '营业中',
    description:
      '强调风味豆与更松弛的空间感，适合替换成更偏“慢坐聊天”的咖啡站，停留感会明显比快取型门店更完整。',
    price: '约 ¥36-52',
    rating: '4.7',
    ratingCount: '618',
    heroWordmark: 'VOLCÁN',
    heroCaption: 'Roastery · Coffee',
    heroMarquee: '风味咖啡',
    heroBackground:
      'linear-gradient(180deg, rgba(21, 15, 14, 0.16) 0%, rgba(21, 15, 14, 0.58) 100%), radial-gradient(110% 100% at 24% 16%, rgba(238, 223, 216, 0.88) 0%, rgba(180, 136, 120, 0.86) 42%, rgba(92, 57, 49, 0.94) 100%)',
    reviews: [
      makeReview('volcan-1', 'Mina', '4 天前', '空间更安静，适合慢慢喝，聊天不会被打断。', 5, '#ecd3ca'),
      makeReview('volcan-2', '大毛', '2 周前', '风味选择比较多，喜欢手冲或豆子口感差异的人会更有乐趣。', 4, '#e4dbc9'),
    ],
    reminders: ['适合慢聊久坐', '适合风味咖啡', '步行略远一点'],
    reminderNote: '如果你打算把第二站变成聊天主场，这家会比快取型咖啡馆更适合。',
  },
  '兰心餐厅（进贤路店）': {
    title: '兰心餐厅（进贤路店）',
    address: '上海市黄浦区进贤路130号附近',
    hours: '周一至周日 11:00-21:00',
    status: '营业中',
    description:
      '老牌本帮菜馆，适合作为第三站的经典晚餐收尾。菜式稳定、节奏明确，如果你希望路线最后一站更“像上海”，这里会更合适。',
    price: '约 ¥70-90',
    rating: '4.7',
    ratingCount: '1326',
    heroWordmark: '兰心',
    heroCaption: 'Shanghai Cuisine',
    heroMarquee: '本帮经典',
    heroBackground:
      'linear-gradient(180deg, rgba(23, 18, 12, 0.14) 0%, rgba(23, 18, 12, 0.58) 100%), radial-gradient(100% 100% at 22% 14%, rgba(245, 225, 196, 0.88) 0%, rgba(192, 138, 92, 0.88) 46%, rgba(109, 62, 28, 0.94) 100%)',
    reviews: [
      makeReview('lanxin-1', '阿润', '3 天前', '味道很稳，适合带外地朋友来吃一顿传统本帮菜。', 5, '#f0dcc2'),
      makeReview('lanxin-2', '晴子', '8 天前', '晚饭点会忙，但如果作为路线收尾，这种热闹感反而挺有城市烟火气。', 4, '#d9e6db'),
    ],
    reminders: ['适合经典收尾', '偏本帮口味', '晚餐点更热闹'],
    reminderNote: '如果你前面已经走了不少路，这一站更建议直接进店吃饭，不必再额外绕去别处。',
  },
  '福和面馆（武康路附近）': {
    title: '福和面馆（武康路附近）',
    address: '上海市徐汇区武康路280号附近',
    hours: '周一至周日 10:30-21:00',
    status: '营业中',
    description:
      '更轻松直接的一站式热汤面馆，节奏比正式餐厅更快，适合把路线尾声收在一顿温热但不过分正式的晚餐上。',
    price: '约 ¥32-48',
    rating: '4.5',
    ratingCount: '579',
    heroWordmark: '福和面馆',
    heroCaption: 'Noodle House',
    heroMarquee: '热汤收尾',
    heroBackground:
      'linear-gradient(180deg, rgba(24, 17, 12, 0.14) 0%, rgba(24, 17, 12, 0.58) 100%), radial-gradient(110% 100% at 25% 16%, rgba(255, 233, 199, 0.88) 0%, rgba(223, 168, 94, 0.86) 44%, rgba(126, 73, 30, 0.94) 100%)',
    reviews: [
      makeReview('fuhe-1', '木木', '2 天前', '汤头舒服，分量刚好，适合走了一下午之后来一碗热面。', 5, '#f3dfc1'),
      makeReview('fuhe-2', '达达', '12 天前', '不需要太多决策，坐下就能吃，路线最后一站选它会很省心。', 4, '#e0e7cd'),
    ],
    reminders: ['适合快速收尾', '热汤更舒服', '不想太正式时很好用'],
    reminderNote: '如果你当天已经喝过咖啡和甜饮，最后换成一份热汤面，体感会更平衡。',
  },
}

function buildFallbackPlaceDetail(summary: PlaceDetailSummary): PlaceDetail {
  const shortTitle = summary.title.replace(/（.*?）/g, '').trim()

  return {
    title: summary.title,
    address: '上海市徐汇区武康路周边',
    hours: '周一至周日 10:00-20:00',
    status: '营业中',
    description: `${summary.title}适合作为这条路线中的一个停留点，节奏不会太赶，适合按当前这站的标签继续慢慢展开。`,
    price: summary.price ?? '人均 ¥50',
    rating: '4.6',
    ratingCount: '526',
    heroWordmark: shortTitle,
    heroCaption: 'Place Detail',
    heroMarquee: (summary.tags && summary.tags[0]) || '路线停留',
    heroBackground:
      'linear-gradient(180deg, rgba(20, 20, 20, 0.14) 0%, rgba(20, 20, 20, 0.56) 100%), radial-gradient(110% 100% at 25% 18%, rgba(238, 234, 227, 0.88) 0%, rgba(192, 179, 165, 0.84) 45%, rgba(98, 85, 72, 0.94) 100%)',
    reviews: [
      makeReview('fallback-1', '旅人', '3 天前', '这站适合顺着路线自然停下来，不需要额外折腾，整体节奏很舒服。', 5, '#e8dfd1'),
      makeReview('fallback-2', '阿青', '1 周前', '如果你想保留一点临场决定的空间，这种类型的地点很合适。', 4, '#d8e1ef'),
    ],
    reminders: summary.tags && summary.tags.length > 0 ? summary.tags.slice(0, 3) : ['适合短暂停留', '适合按路线顺走', '适合临场调整'],
    reminderNote: '如果你临时替换了站点，这个详情页会优先展示当前地点的基础信息。',
  }
}

export function resolvePlaceDetail(summary: PlaceDetailSummary): PlaceDetail {
  return placeDetailsByTitle[summary.title] ?? buildFallbackPlaceDetail(summary)
}