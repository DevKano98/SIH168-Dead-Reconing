package ai.continuum.idr

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import android.util.AttributeSet
import android.view.MotionEvent
import android.view.ScaleGestureDetector
import android.view.View
import kotlin.math.cos
import kotlin.math.sin

/**
 * Lightweight, zero-dependency offline vector road network canvas.
 * Renders topological road segments, vehicle trajectory history,
 * dead-reckoning uncertainty ellipse, heading arrow, and scale bar.
 */
class MapView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyleAttr: Int = 0
) : View(context, attrs, defStyleAttr) {

    private var roadPack: RoadGraphPack? = null

    // Vehicle state
    private var vehicleLat: Double? = null
    private var vehicleLon: Double? = null
    private var vehicleHeadingDeg: Float = 0f
    private var vehicleUncertaintyM: Float = 5f
    private var isFallbackActive: Boolean = false

    // Trajectory breadcrumbs
    private val breadcrumbs = ArrayList<Pair<Double, Double>>() // (lat, lon)
    private val maxBreadcrumbs = 500

    // Canvas transformation (pan and zoom)
    private var scale = 2.0f // pixels per meter
    private var centerEastM = 0.0
    private var centerNorthM = 0.0
    private var autoFollowVehicle = true

    // Gesture detection
    private var lastTouchX = 0f
    private var lastTouchY = 0f
    private var isPanning = false

    private val scaleDetector = ScaleGestureDetector(context, object : ScaleGestureDetector.SimpleOnScaleGestureListener() {
        override fun onScale(detector: ScaleGestureDetector): Boolean {
            scale = (scale * detector.scaleFactor).coerceIn(0.1f, 20.0f)
            invalidate()
            return true
        }
    })

    // Paints
    private val bgPaint = Paint().apply { color = Color.parseColor("#0F172A") } // Slate 900
    private val motorwayPaint = Paint().apply {
        color = Color.parseColor("#38BDF8") // Sky 400
        strokeWidth = 6f
        style = Paint.Style.STROKE
        isAntiAlias = true
    }
    private val primaryRoadPaint = Paint().apply {
        color = Color.parseColor("#94A3B8") // Slate 400
        strokeWidth = 4f
        style = Paint.Style.STROKE
        isAntiAlias = true
    }
    private val serviceRoadPaint = Paint().apply {
        color = Color.parseColor("#475569") // Slate 600
        strokeWidth = 2.5f
        style = Paint.Style.STROKE
        isAntiAlias = true
    }
    private val trailPaint = Paint().apply {
        color = Color.parseColor("#F59E0B") // Amber 500
        strokeWidth = 3f
        style = Paint.Style.STROKE
        isAntiAlias = true
    }
    private val vehiclePaint = Paint().apply {
        color = Color.parseColor("#10B981") // Emerald 500 (GNSS)
        style = Paint.Style.FILL
        isAntiAlias = true
    }
    private val vehicleFallbackPaint = Paint().apply {
        color = Color.parseColor("#EF4444") // Red 500 (Fallback)
        style = Paint.Style.FILL
        isAntiAlias = true
    }
    private val uncertaintyPaint = Paint().apply {
        color = Color.parseColor("#3338BDF8") // Sky translucent
        style = Paint.Style.FILL
        isAntiAlias = true
    }
    private val uncertaintyStrokePaint = Paint().apply {
        color = Color.parseColor("#38BDF8")
        style = Paint.Style.STROKE
        strokeWidth = 1.5f
        isAntiAlias = true
    }
    private val textPaint = Paint().apply {
        color = Color.WHITE
        textSize = 28f
        isAntiAlias = true
    }
    private val scaleBarPaint = Paint().apply {
        color = Color.WHITE
        strokeWidth = 4f
        style = Paint.Style.STROKE
        isAntiAlias = true
    }

    private val headingPath = Path()

    fun setRoadPack(pack: RoadGraphPack) {
        this.roadPack = pack
        if (pack.nodes.isNotEmpty()) {
            val firstNode = pack.nodes.values.first()
            centerEastM = firstNode.eastM
            centerNorthM = firstNode.northM
        }
        invalidate()
    }

    fun updateVehicle(lat: Double, lon: Double, headingDeg: Float, uncertaintyM: Float, isFallback: Boolean) {
        this.vehicleLat = lat
        this.vehicleLon = lon
        this.vehicleHeadingDeg = headingDeg
        this.vehicleUncertaintyM = uncertaintyM
        this.isFallbackActive = isFallback

        breadcrumbs.add(Pair(lat, lon))
        if (breadcrumbs.size > maxBreadcrumbs) {
            breadcrumbs.removeAt(0)
        }

        if (autoFollowVehicle && roadPack != null) {
            val (ve, vn) = roadPack!!.toEnu(lat, lon)
            centerEastM = ve
            centerNorthM = vn
        }
        invalidate()
    }

    fun setAutoFollow(follow: Boolean) {
        this.autoFollowVehicle = follow
        invalidate()
    }

    override fun onTouchEvent(event: MotionEvent): Boolean {
        scaleDetector.onTouchEvent(event)

        when (event.actionMasked) {
            MotionEvent.ACTION_DOWN -> {
                lastTouchX = event.x
                lastTouchY = event.y
                isPanning = true
            }
            MotionEvent.ACTION_MOVE -> {
                if (!scaleDetector.isInProgress && isPanning) {
                    val dx = event.x - lastTouchX
                    val dy = event.y - lastTouchY
                    centerEastM -= dx / scale
                    centerNorthM += dy / scale // North is up (screen Y is down)
                    lastTouchX = event.x
                    lastTouchY = event.y
                    autoFollowVehicle = false
                    invalidate()
                }
            }
            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                isPanning = false
            }
        }
        return true
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        canvas.drawPaint(bgPaint)

        val w = width.toFloat()
        val h = height.toFloat()
        val midX = w / 2f
        val midY = h / 2f

        val pack = roadPack ?: run {
            canvas.drawText("Offline Map: No road network loaded", 40f, 60f, textPaint)
            return
        }

        // Draw Road Segments
        for (seg in pack.segments.values) {
            val sx = midX + ((seg.startEastM - centerEastM) * scale).toFloat()
            val sy = midY - ((seg.startNorthM - centerNorthM) * scale).toFloat()
            val ex = midX + ((seg.endEastM - centerEastM) * scale).toFloat()
            val ey = midY - ((seg.endNorthM - centerNorthM) * scale).toFloat()

            val paint = when (seg.roadType) {
                "motorway" -> motorwayPaint
                "service" -> serviceRoadPaint
                else -> primaryRoadPaint
            }
            canvas.drawLine(sx, sy, ex, ey, paint)
        }

        // Draw Trajectory Trail
        if (breadcrumbs.size >= 2) {
            for (i in 1 until breadcrumbs.size) {
                val (pLat1, pLon1) = breadcrumbs[i - 1]
                val (pLat2, pLon2) = breadcrumbs[i]
                val (e1, n1) = pack.toEnu(pLat1, pLon1)
                val (e2, n2) = pack.toEnu(pLat2, pLon2)
                val x1 = midX + ((e1 - centerEastM) * scale).toFloat()
                val y1 = midY - ((n1 - centerNorthM) * scale).toFloat()
                val x2 = midX + ((e2 - centerEastM) * scale).toFloat()
                val y2 = midY - ((n2 - centerNorthM) * scale).toFloat()
                canvas.drawLine(x1, y1, x2, y2, trailPaint)
            }
        }

        // Draw Vehicle
        val vLat = vehicleLat
        val vLon = vehicleLon
        if (vLat != null && vLon != null) {
            val (ve, vn) = pack.toEnu(vLat, vLon)
            val vx = midX + ((ve - centerEastM) * scale).toFloat()
            val vy = midY - ((vn - centerNorthM) * scale).toFloat()

            // Uncertainty circle
            val uncertRadiusPx = (vehicleUncertaintyM * scale).coerceAtLeast(8f)
            canvas.drawCircle(vx, vy, uncertRadiusPx, uncertaintyPaint)
            canvas.drawCircle(vx, vy, uncertRadiusPx, uncertaintyStrokePaint)

            // Vehicle Marker with directional cone
            val headingRad = Math.toRadians(vehicleHeadingDeg.toDouble())
            val markerSize = 22f

            headingPath.reset()
            val tipX = vx + (markerSize * 1.5f * sin(headingRad)).toFloat()
            val tipY = vy - (markerSize * 1.5f * cos(headingRad)).toFloat()
            val leftX = vx + (markerSize * sin(headingRad + 2.5)).toFloat()
            val leftY = vy - (markerSize * cos(headingRad + 2.5)).toFloat()
            val rightX = vx + (markerSize * sin(headingRad - 2.5)).toFloat()
            val rightY = vy - (markerSize * cos(headingRad - 2.5)).toFloat()

            headingPath.moveTo(tipX, tipY)
            headingPath.lineTo(leftX, leftY)
            headingPath.lineTo(vx, vy)
            headingPath.lineTo(rightX, rightY)
            headingPath.close()

            val vPaint = if (isFallbackActive) vehicleFallbackPaint else vehiclePaint
            canvas.drawPath(headingPath, vPaint)
        }

        // Status Overlay Header
        val packLabel = "Map: ${pack.name} (${pack.segments.size} segments)"
        canvas.drawText(packLabel, 30f, 45f, textPaint)

        // Draw Scale Bar at bottom right
        val targetBarMeters = (100f / scale).coerceIn(10f, 1000f)
        val roundedMeters = when {
            targetBarMeters < 25 -> 20
            targetBarMeters < 75 -> 50
            targetBarMeters < 150 -> 100
            targetBarMeters < 350 -> 250
            targetBarMeters < 750 -> 500
            else -> 1000
        }
        val barWidthPx = roundedMeters * scale
        val barRight = w - 40f
        val barLeft = barRight - barWidthPx
        val barY = h - 40f

        canvas.drawLine(barLeft, barY, barRight, barY, scaleBarPaint)
        canvas.drawLine(barLeft, barY - 10f, barLeft, barY + 10f, scaleBarPaint)
        canvas.drawLine(barRight, barY - 10f, barRight, barY + 10f, scaleBarPaint)
        val scaleText = "${roundedMeters}m"
        val textWidth = textPaint.measureText(scaleText)
        canvas.drawText(scaleText, barLeft + (barWidthPx - textWidth) / 2f, barY - 15f, textPaint)
    }
}
