export type RouteEndpointId = 'start' | 'end'

export type RoutePointId =
  | 'filmBookstore'
  | 'racBar'
  | 'springNoodle'
  | 'duozhuayu'
  | 'hengshanheji'
  | 'mannerAnfu'
  | 'cafeDelVolcan'
  | 'lanxin'
  | 'fuheNoodle'

export type RouteNodeId = RouteEndpointId | RoutePointId

export type RoutePoint = {
  x: number
  y: number
}

export const routePointMap: Record<RouteNodeId, RoutePoint> = {
  start: { x: 128, y: 407 },
  filmBookstore: { x: 154, y: 333 },
  duozhuayu: { x: 144, y: 314 },
  hengshanheji: { x: 214, y: 238 },
  racBar: { x: 232, y: 224 },
  mannerAnfu: { x: 246, y: 210 },
  cafeDelVolcan: { x: 270, y: 194 },
  springNoodle: { x: 314, y: 253 },
  lanxin: { x: 328, y: 271 },
  fuheNoodle: { x: 287, y: 262 },
  end: { x: 372, y: 234 },
}

const baselineRoute: RoutePointId[] = ['filmBookstore', 'racBar', 'springNoodle']
const itineraryBaselineKilometers = 1.8
const itineraryBaselineWalkMinutes = 25
const baselineSegmentCount = baselineRoute.length + 1

function getPoint(id: RouteNodeId) {
  return routePointMap[id]
}

function getPixelDistance(from: RouteNodeId, to: RouteNodeId) {
  const startPoint = getPoint(from)
  const endPoint = getPoint(to)
  return Math.hypot(endPoint.x - startPoint.x, endPoint.y - startPoint.y)
}

function getRoutePixelDistance(routePointIds: RoutePointId[]) {
  const nodeIds = ['start', ...routePointIds, 'end'] as RouteNodeId[]
  let totalPixels = 0

  for (let index = 1; index < nodeIds.length; index += 1) {
    totalPixels += getPixelDistance(nodeIds[index - 1], nodeIds[index])
  }

  return totalPixels
}

export const itinerarySegmentAccessKilometers = 0.08
export const itineraryKilometersPerPixel =
  (itineraryBaselineKilometers - baselineSegmentCount * itinerarySegmentAccessKilometers) / getRoutePixelDistance(baselineRoute)
export const itineraryWalkMinutesPerKilometer = itineraryBaselineWalkMinutes / itineraryBaselineKilometers

export function getRouteNodeIds(routePointIds: RoutePointId[]) {
  return ['start', ...routePointIds, 'end'] as RouteNodeId[]
}

export function getRouteSegment(from: RouteNodeId, to: RouteNodeId) {
  const pixelDistance = getPixelDistance(from, to)
  const distanceKm = pixelDistance * itineraryKilometersPerPixel + itinerarySegmentAccessKilometers
  const walkMinutes = distanceKm * itineraryWalkMinutesPerKilometer

  return {
    pixelDistance,
    distanceKm,
    walkMinutes,
  }
}

export function getTotalRouteMetrics(routePointIds: RoutePointId[]) {
  const nodeIds = getRouteNodeIds(routePointIds)

  return nodeIds.slice(1).reduce(
    (totals, nodeId, index) => {
      const segment = getRouteSegment(nodeIds[index], nodeId)
      return {
        distanceKm: totals.distanceKm + segment.distanceKm,
        walkMinutes: totals.walkMinutes + segment.walkMinutes,
      }
    },
    {
      distanceKm: 0,
      walkMinutes: 0,
    },
  )
}
