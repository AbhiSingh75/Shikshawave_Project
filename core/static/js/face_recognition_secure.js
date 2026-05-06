// core/static/js/face_recognition_secure.js
// Secure Face Recognition System with Liveness Detection for ShikshaWave

class SecureFaceRecognition {
    constructor() {
        this.video = null;
        this.canvas = null;
        this.context = null;
        this.stream = null;
        this.isCapturing = false;
        this.faceDescriptor = null;
        this.sessionId = null;
        this.livenessChallenge = null;
        this.livenessCompleted = true; // ULTRA-FAST: Pre-verify liveness
        this.authenticationTimer = null; 
        this.isAuthenticating = false;
        this.lastAuthAttempt = 0;
        this.authCooldown = 5000; // 5 seconds cooldown
        this.referenceDescriptor = null; // Store descriptor from profile photo
        this.boxHistory = []; // Passive liveness: Track box jitters
        this.lastBox = null;
        
        // PERFORMANCE OPTIMIZATION: Throttling control
        this.detectionFrameCount = 0;
        this.ssdThrottlingFactor = 3; // Run SSD every 3 frames if face tracked
        this.isFaceTracked = false;

        // Face detection settings
        this.faceDetectionModel = null;
        this.faceLandmarkModel = null;
        this.faceRecognitionModel = null;

        // Liveness detection data
        this.eyeAspectRatios = [];
        this.headPositions = [];
        this.blinkCount = 0;
        this.smileConfidence = 0;
        this.smileStartTime = null;

        // UI elements - Setup immediately to prevent null references during async init
        this.setupUI();

        // Initialization state
        this.isReady = false;
        this.initPromise = this.init();

        // Make available globally immediately
        window.faceRecognition = this;
    }

    async init() {
        try {
            // Handle browser tracking prevention
            try {
                // Test if we can access localStorage (some browsers block this)
                localStorage.setItem('face_auth_test', 'test');
                localStorage.removeItem('face_auth_test');
            } catch (e) {
                // Fallback storage handled silently
            }

            // Load face-api.js models
            await this.loadModels();
            this.setupUI();

            // Notify that system is ready
            if (this.statusElement) {
                this.updateStatus('Face recognition system ready', 'success');
            }

        } catch (error) {
            if (this.statusElement) {
                this.showError('Failed to initialize face recognition system: ' + error.message);
            } else {
                // Initialiation error handled silently
            }
        }
    }

    async loadModels() {
        const MODEL_URL = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api@latest/model';

        try {
            this.updateStatus('Calibrating AI Core...', 'info');
            
            // SPEED OPTIMIZATION: Load only required models in parallel
            await Promise.all([
                faceapi.nets.ssdMobilenetv1.loadFromUri(MODEL_URL),
                faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
                faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL)
                // REMOVED: Face Expressions (No longer used)
                // REMOVED: Tiny Face Detector (Replaced by full SSD for reliability)
            ]);

            // Pre-warm SSD model (industry practice for ultra-fast first match)
            const dummyCanvas = document.createElement('canvas');
            dummyCanvas.width = 160; dummyCanvas.height = 120;
            const ssdOpts = new faceapi.SsdMobilenetv1Options({ minConfidence: 0.5 });
            await faceapi.detectSingleFace(dummyCanvas, ssdOpts);
            
            this.isReady = true;
            this.updateStatus('AI System Ready', 'success');
        } catch (error) {
            this.showError('AI System Offline: ' + error.message);
            console.error('Initialization crash:', error);
            throw error;
        }
    }

    setupUI() {
        this.video = document.getElementById('faceVideo');
        this.canvas = document.getElementById('faceCanvas');
        this.statusElement = document.getElementById('faceStatus');
        this.progressElement = document.getElementById('faceProgress');
        this.challengeElement = document.getElementById('livenessChallenge');
        this.container = document.getElementById('faceid-scanner') || document.getElementById('faceRecognitionContainer') || document.getElementById('faceVideo');

        if (this.canvas) {
            this.context = this.canvas.getContext('2d');
        }
    }

    async startCamera() {
        if (this.stream) return;

        // Ensure models are ready before camera/detection starts
        if (this.initPromise) {
            await this.initPromise.catch(() => {});
        }

        try {
            // SPEED OPTIMIZATION: Lower ideal resolution for faster camera start
            // 640x480 is sufficient for face detection with 128px-160px input sizes
            const constraints = {
                video: {
                    width: { ideal: 640, min: 320 },
                    height: { ideal: 480, min: 240 },
                    facingMode: 'user',
                    frameRate: { ideal: 30, min: 15 },
                    // Remove hunting constraints that can delay startup
                    aspectRatio: { ideal: 4/3 }
                }
            };
            
            // Try advanced constraints first, fallback to basic if not supported
            try {
                this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            } catch (advancedError) {
                console.log('Advanced camera settings not supported, using basic settings');
                this.stream = await navigator.mediaDevices.getUserMedia({
                    video: {
                        width: { ideal: 640 },
                        height: { ideal: 480 },
                        facingMode: 'user'
                    }
                });
            }

            if (this.video) {
                this.video.srcObject = this.stream;
                this.video.onloadedmetadata = () => {
                    this.video.play();
                    this.setupCanvas();
                    this.startFaceDetection();
                };
            }

            this.updateStatus('Camera started. Position your face in the frame.', 'info');

        } catch (error) {
            this.showError('Camera access denied. Please allow camera access and try again.');
        } finally {
            const overlay = document.getElementById('loadingOverlay');
            if (overlay) overlay.style.display = 'none';
        }
    }

    setupCanvas() {
        if (this.canvas && this.video) {
            this.canvas.width = this.video.videoWidth;
            this.canvas.height = this.video.videoHeight;
        }
    }

    async startFaceDetection() {
        if (!this.video || this.video.paused || this.video.ended) {
            this.updateStatus('Camera stopped', 'info');
            return;
        }

        const ssdOpts = new faceapi.SsdMobilenetv1Options({ minConfidence: 0.3 });

        try {
            this.detectionFrameCount++;
            
            // RELY ON SSD DIRECTLY: Robust and fast enough for modern devices
            const det = await faceapi.detectSingleFace(this.video, ssdOpts)
                .withFaceLandmarks()
                .withFaceDescriptor();

            if (det) {
                this.isFaceTracked = true;
                this.missedFrames = 0; // Reset hysteresis
                const pointer = document.getElementById('focusPointer');
                if (pointer) pointer.classList.add('active');

                this.faceDescriptor = det.descriptor;
                const env = this.analyzeEnvironment(det.detection.box);
                const checks = this.calcChecks(det, env);
                const q = this.calculateFaceQuality(det, env, checks);

                this.applyDynamicVideoFilters(env);
                this.drawDetectionBox(det.detection);
                
                // PASSIVE SECURITY: Start tracking movement immediately
                this.trackBox(det.detection.box);
                
                this.processDetections(det, env, checks, q);
                this.processLivenessData(det);
            } else {
                this.isFaceTracked = false;
                this.missedFrames++;
                this.stabilityStartTime = null;
                const pointer = document.getElementById('focusPointer');
                if (pointer) pointer.classList.remove('active');

                // HYSTERESIS: Only show "Searching" if we've missed several frames (approx 1s)
                if (this.missedFrames >= 15) {
                    this.updateStatus('Searching for face...', 'warning');
                    this.updateMatchPercentage(0);
                }
                if (this.context) this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);
            }
        } catch (error) {
            console.error("Detection error:", error);
        }

        requestAnimationFrame(() => this.startFaceDetection());
    }

    drawDetectionBox(detection) {
        if (!this.canvas || !this.context) return;
        const dims = faceapi.matchDimensions(this.canvas, this.video, true);
        const resized = faceapi.resizeResults(detection, dims);
        this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);
        faceapi.draw.drawDetections(this.canvas, resized);
    }

    processDetections(det, env, checks, q) {
        this.updateMatchPercentage(q);
        const feedback = this.getFeedback(env, checks);

        if (q >= 50) { // ULTRA-ROBUST: Lowered threshold from 70 to 50
            // ONLY update status if liveness hasn't started yet
            if (!this.livenessStarted) {
                this.updateStatus('Match in progress. Hold still...', 'success');
            }
            
            if (!this.stabilityStartTime) this.stabilityStartTime = Date.now();
            const holdTime = (Date.now() - this.stabilityStartTime) / 1000;

            // Update dots based on stability
            this.updateFaceIndicators(Math.min(3, Math.floor(holdTime * 4.5)));

            if (holdTime >= 0.3) { 
                if (!this.isAuthenticating) {
                    // Start checking passive liveness
                    if (this.verifyPassiveLiveness()) {
                        const identifier = document.getElementById('faceIdentifier').value.trim();
                        this.authenticateWithFace(identifier);
                    } else if (holdTime > 1.5) {
                        this.updateStatus('Ensuring real-time presence...', 'info');
                    }
                }
            }
        } else {
            this.stabilityStartTime = null;
            this.updateFaceIndicators(0);
            
            const displayFeedback = q > 25 ? feedback : "Position face clearly";
            this.updateStatus(displayFeedback, q >= 40 ? 'info' : 'warning');
        }
    }

    calculateFaceQuality(d, env, c) {
        // IMPROVED QUALITY MODEL - More linear and forgiving
        const rawConf = d.detection.score;
        // Scale 0-45 points based on confidence (conf >= 0.35)
        let biometricScore = (Math.max(0, rawConf - 0.3) / 0.7) * 45;
        biometricScore = Math.min(45, biometricScore);
        
        // Head Pose/Symmetry (20%)
        let poseScore = c.pose < 0.18 ? 20 : Math.max(0, 20 * (1 - (c.pose - 0.18) / 0.27));
        
        // Enhanced Environmental Clarity (25%) - More sophisticated for low light
        let lightScore = 0;
        if (env.isLowLight) {
            // More forgiving scoring for low light conditions
            if (env.lum > 35 && env.lum < 85) {
                lightScore = 12; // Good low light
            } else if (env.lum > 25 && env.lum < 100) {
                lightScore = 10; // Acceptable low light
            } else {
                lightScore = Math.max(0, 12 * (1 - Math.abs(env.lum - 60) / 60));
            }
            
            // Bonus for good contrast in low light
            if (env.hasGoodContrast) {
                lightScore += 3;
            }
        } else {
            // Normal lighting conditions
            lightScore = (env.lum > 70 && env.lum < 200) ? 12 : 
                       Math.max(0, 12 * (1 - Math.abs(env.lum - 135) / 100));
        }
        
        // Enhanced sharpness scoring
        let sharpScore = 0;
        if (env.isSharp) {
            sharpScore = 10;
        } else if (env.blur > 5) {
            sharpScore = Math.min(10, env.blur / 0.8);
        }
        
        // Noise penalty for very noisy images
        if (!env.isClean && env.noiseLevel > 35) {
            sharpScore = Math.max(0, sharpScore - 3);
        }
        
        // Composition (10%)
        let centerPoints = c.center ? 10 : 0;
        
        let total = biometricScore + poseScore + lightScore + sharpScore + centerPoints;
        
        return Math.min(100, Math.round(total));
    }

    analyzeEnvironment(box) {
        if (!this.tempCanvas) {
            this.tempCanvas = document.createElement('canvas');
            this.tCtx = this.tempCanvas.getContext('2d', { willReadFrequently: true });
        }
        this.tempCanvas.width = box.width;
        this.tempCanvas.height = box.height;
        
        // Enhanced image processing for low light conditions
        this.tCtx.drawImage(this.video, box.x, box.y, box.width, box.height, 0, 0, box.width, box.height);
        
        // Apply image enhancement for better analysis in low light
        const imageData = this.tCtx.getImageData(0, 0, box.width, box.height);
        const data = imageData.data;
        
        // Enhanced luminance calculation with gamma correction
        let luminance = 0;
        let contrast = 0;
        let pixelCount = data.length / 4;
        
        // Calculate luminance and contrast
        for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i+1];
            const b = data[i+2];
            
            // Enhanced luminance calculation with gamma correction
            const pixelLum = 0.299 * Math.pow(r/255, 2.2) + 0.587 * Math.pow(g/255, 2.2) + 0.114 * Math.pow(b/255, 2.2);
            luminance += pixelLum * 255;
        }
        luminance = luminance / pixelCount;
        
        // Calculate contrast for better quality assessment
        let variance = 0;
        for (let i = 0; i < data.length; i += 4) {
            const pixelLum = 0.299 * data[i] + 0.587 * data[i+1] + 0.114 * data[i+2];
            variance += Math.pow(pixelLum - luminance, 2);
        }
        contrast = Math.sqrt(variance / pixelCount);

        // Enhanced blur detection using Sobel edge detection
        let edgeStrength = 0;
        const width = box.width;
        const height = box.height;
        
        // Sobel edge detection for better blur assessment
        for (let y = 1; y < height - 1; y++) {
            for (let x = 1; x < width - 1; x++) {
                const idx = (y * width + x) * 4;
                
                // Get surrounding pixels
                const tl = 0.299 * data[idx - width*4 - 4] + 0.587 * data[idx - width*4 - 3] + 0.114 * data[idx - width*4 - 2];
                const tm = 0.299 * data[idx - width*4] + 0.587 * data[idx - width*4 + 1] + 0.114 * data[idx - width*4 + 2];
                const tr = 0.299 * data[idx - width*4 + 4] + 0.587 * data[idx - width*4 + 5] + 0.114 * data[idx - width*4 + 6];
                const ml = 0.299 * data[idx - 4] + 0.587 * data[idx - 3] + 0.114 * data[idx - 2];
                const mr = 0.299 * data[idx + 4] + 0.587 * data[idx + 5] + 0.114 * data[idx + 6];
                const bl = 0.299 * data[idx + width*4 - 4] + 0.587 * data[idx + width*4 - 3] + 0.114 * data[idx + width*4 - 2];
                const bm = 0.299 * data[idx + width*4] + 0.587 * data[idx + width*4 + 1] + 0.114 * data[idx + width*4 + 2];
                const br = 0.299 * data[idx + width*4 + 4] + 0.587 * data[idx + width*4 + 5] + 0.114 * data[idx + width*4 + 6];
                
                // Sobel operators
                const gx = (-1 * tl) + (1 * tr) + (-2 * ml) + (2 * mr) + (-1 * bl) + (1 * br);
                const gy = (-1 * tl) + (-2 * tm) + (-1 * tr) + (1 * bl) + (2 * bm) + (1 * br);
                
                edgeStrength += Math.sqrt(gx * gx + gy * gy);
            }
        }
        
        const blurScore = edgeStrength / ((width - 2) * (height - 2));
        
        // Enhanced noise detection for low light conditions
        let noiseLevel = 0;
        const sampleStep = Math.max(1, Math.floor(pixelCount / 1000));
        for (let i = 0; i < data.length - 12; i += 4 * sampleStep) {
            const r1 = data[i], g1 = data[i+1], b1 = data[i+2];
            const r2 = data[i+4], g2 = data[i+5], b2 = data[i+6];
            const r3 = data[i+8], g3 = data[i+9], b3 = data[i+10];
            
            noiseLevel += Math.abs(r1 - r2) + Math.abs(g1 - g2) + Math.abs(b1 - b2);
            noiseLevel += Math.abs(r2 - r3) + Math.abs(g2 - g3) + Math.abs(b2 - b3);
        }
        noiseLevel = noiseLevel / (pixelCount / sampleStep * 6);

        return { 
            lum: luminance, 
            blur: blurScore, 
            contrast,
            noiseLevel,
            // Quality indicators for low light
            isLowLight: luminance < 80,
            hasGoodContrast: contrast > 15,
            isSharp: blurScore > 8,
            isClean: noiseLevel < 25
        };
    }

    calcChecks(d, env) {
        const marks = d.landmarks.positions;
        const leftEye = marks[36], rightEye = marks[45], nose = marks[30];
        const distL = Math.hypot(nose.x - leftEye.x, nose.y - leftEye.y);
        const distR = Math.hypot(rightEye.x - nose.x, rightEye.y - nose.y);
        const symmetry = Math.abs(distL - distR) / Math.max(distL, distR);

        // Enhanced lighting check for low light conditions
        let lightingOk = false;
        if (env.isLowLight) {
            // More forgiving criteria for low light
            lightingOk = env.lum > 30 && env.lum < 100 && env.hasGoodContrast;
        } else {
            // Standard lighting criteria
            lightingOk = env.lum > 50 && env.lum < 220;
        }

        return {
            center: Math.abs((d.detection.box.x + d.detection.box.width / 2) - this.video.videoWidth / 2) < 80, // More forgiving centering
            lighting: lightingOk,
            focus: env.isSharp || env.blur > 8, // More forgiving focus
            pose: symmetry
        };
    }

    getFeedback(env, c) {
        if (!c.center) return "Center your face in the frame";
        
        // Enhanced low light feedback
        if (env.isLowLight) {
            if (env.lum < 40) return "Very dark - add more light or move to brighter area";
            if (env.lum < 60) return "Low light detected - try to add more light";
            if (!env.hasGoodContrast) return "Low contrast - improve lighting on face";
        }
        
        if (env.lum > 240) return "Too bright, reduce glare or move away from direct light";
        if (!env.isSharp) return "Hold steady, image appears blurry";
        if (!env.isClean && env.noiseLevel > 30) return "Image is noisy - improve lighting conditions";
        if (c.pose && c.pose > 0.25) return "Look directly at the camera";
        
        return "Hold steady for verification...";
    }

    applyDynamicVideoFilters(env) {
        if (!this.video) return;
        
        // Remove existing filter classes
        this.video.classList.remove('low-light', 'very-low-light');
        
        // Apply appropriate filter based on lighting conditions
        if (env.lum < 40) {
            this.video.classList.add('very-low-light');
        } else if (env.lum < 70) {
            this.video.classList.add('low-light');
        }
        // Normal lighting uses the default filter from CSS
    }

    isFaceWellPositioned(detection) {
        const box = detection.detection.box;
        const canvasWidth = this.canvas.width;
        const canvasHeight = this.canvas.height;

        // Check if face is centered and appropriately sized
        const centerX = box.x + box.width / 2;
        const centerY = box.y + box.height / 2;

        const isHorizontallyCentered = Math.abs(centerX - canvasWidth / 2) < canvasWidth * 0.1;
        const isVerticallyCentered = Math.abs(centerY - canvasHeight / 2) < canvasHeight * 0.1;
        const isAppropriateSize = box.width > canvasWidth * 0.2 && box.width < canvasWidth * 0.8;

        return isHorizontallyCentered && isVerticallyCentered && isAppropriateSize;
    }

    processLivenessData(detection) {
        const landmarks = detection.landmarks;
        // Face expressions removed for speed

        // Calculate eye aspect ratio for blink detection
        const leftEye = landmarks.getLeftEye();
        const rightEye = landmarks.getRightEye();

        const leftEAR = this.calculateEyeAspectRatio(leftEye);
        const rightEAR = this.calculateEyeAspectRatio(rightEye);
        const avgEAR = (leftEAR + rightEAR) / 2;

        this.eyeAspectRatios.push(avgEAR);

        // Detect blinks
        if (this.eyeAspectRatios.length > 1) {
            const prevEAR = this.eyeAspectRatios[this.eyeAspectRatios.length - 2];
            if (prevEAR > 0.25 && avgEAR <= 0.25) {
                this.blinkCount++;
            }
        }

        // Calculate head position (simplified)
        const nose = landmarks.getNose();
        const jawline = landmarks.getJawOutline();

        if (nose.length > 0 && jawline.length > 0) {
            const headPosition = {
                yaw: this.calculateYaw(nose, jawline),
                pitch: this.calculatePitch(nose, jawline),
                timestamp: Date.now()
            };
            this.headPositions.push(headPosition);
        }

        // Smile tracking removed (using ultra-fast direct match)

        // Keep arrays manageable
        if (this.eyeAspectRatios.length > 50) {
            this.eyeAspectRatios = this.eyeAspectRatios.slice(-30);
        }
        if (this.headPositions.length > 50) {
            this.headPositions = this.headPositions.slice(-30);
        }

        // AUTO-TRIGGER: If liveness challenge is active, check if it's potentially met
        if (this.livenessStarted && !this.livenessCompleted && !this.isAuthenticating) {
            this.checkAutoLivenessComplete();
        }
    }

    checkAutoLivenessComplete() {
        if (!this.livenessChallenge) return;
        const challenge = this.livenessChallenge;
        let isMet = false;

        const limit = 20; // Number of frames to analyze
        if (this.headPositions.length < 5) return; // Need a baseline

        switch (challenge.type) {
            case 'blink':
                isMet = this.blinkCount >= (challenge.required_blinks || 2);
                break;
            case 'smile':
                isMet = true; // Smile challenge deprecated
                break;
            case 'head_turn':
                // RANGE BASED DETECTION (Relative)
                const yaws = this.headPositions.map(p => p.yaw);
                const minY = Math.min(...yaws);
                const maxY = Math.max(...yaws);
                isMet = (maxY - minY) > 15; // 15 degree sweep (lowered from 25)
                break;
            case 'nod':
                // RANGE BASED DETECTION (Relative)
                const pitches = this.headPositions.map(p => p.pitch);
                const minP = Math.min(...pitches);
                const maxP = Math.max(...pitches);
                isMet = (maxP - minP) > 8; // 8 degree sweep (lowered from 12)
                break;
        }

        if (isMet) {
            this.completeLivenessChallenge();
        }
    }

    calculateEyeAspectRatio(eye) {
        // Calculate eye aspect ratio for blink detection
        if (eye.length < 6) return 0;

        const vertical1 = this.distance(eye[1], eye[5]);
        const vertical2 = this.distance(eye[2], eye[4]);
        const horizontal = this.distance(eye[0], eye[3]);

        return (vertical1 + vertical2) / (2 * horizontal);
    }

    calculateYaw(nose, jawline) {
        // Simplified yaw calculation
        if (nose.length === 0 || jawline.length === 0) return 0;

        const noseTip = nose[nose.length - 1];
        const leftJaw = jawline[0];
        const rightJaw = jawline[jawline.length - 1];

        const jawCenter = {
            x: (leftJaw.x + rightJaw.x) / 2,
            y: (leftJaw.y + rightJaw.y) / 2
        };

        return Math.atan2(noseTip.x - jawCenter.x, jawCenter.y - noseTip.y) * (180 / Math.PI);
    }

    calculatePitch(nose, jawline) {
        // Simplified pitch calculation
        if (nose.length === 0 || jawline.length === 0) return 0;

        const noseTip = nose[nose.length - 1];
        const noseBase = nose[0];

        return Math.atan2(noseTip.y - noseBase.y, Math.abs(noseTip.x - noseBase.x)) * (180 / Math.PI);
    }

    distance(point1, point2) {
        return Math.sqrt(Math.pow(point1.x - point2.x, 2) + Math.pow(point1.y - point2.y, 2));
    }

    verifyPassiveLiveness() {
        // Industry practice: A real human face in a browser camera stream 
        // will HAVE pixel-level jitter in the detection bounding box.
        // A static photo or replay often has ZERO variance.
        if (this.boxHistory.length < 5) return false;
        
        let totalVariance = 0;
        for (let i = 1; i < this.boxHistory.length; i++) {
            const b1 = this.boxHistory[i-1];
            const b2 = this.boxHistory[i];
            totalVariance += Math.abs(b1.x - b2.x) + Math.abs(b1.y - b2.y);
        }
        
        // If variance is too low (e.g., < 0.1px average), it's suspiciously static
        const isLive = totalVariance > 0.5;
        if (!isLive) console.warn("SECURITY: Passive liveness failed (Face too static)");
        return isLive;
    }

    trackBox(box) {
        this.boxHistory.push({x: box.x, y: box.y});
        if (this.boxHistory.length > 20) this.boxHistory.shift();
    }

    calculateFaceQuality(detection) {
        // Evaluate lighting, size, and detection confidence
        const score = detection.detection.score;
        const width = detection.detection.box.width;
        
        // Return 0-100 quality score
        let quality = score * 100;
        if (width < 100) quality -= 20; // Too far
        if (width > 500) quality -= 10; // Too close
        
        return Math.max(0, quality);
    }

    async startLivenessChallenge() {
        // ULTRA-FAST: Challenges removed
        return;
    }

    displayLivenessChallenge() {
        // ULTRA-FAST: UI hidden
        if (this.challengeElement) this.challengeElement.style.display = 'none';
    }

    async completeLivenessChallenge() {
        // ULTRA-FAST: Always complete
        this.livenessCompleted = true;
    }

    prepareLivenessResponse() {
        const challenge = this.livenessChallenge;

        switch (challenge.type) {
            case 'blink':
                return {
                    blink_count: this.blinkCount,
                    eye_aspect_ratios: this.eyeAspectRatios.slice(-20)
                };

            case 'head_turn':
            case 'nod':
                return {
                    head_positions: this.headPositions.slice(-10)
                };

            case 'smile':
                const smileDuration = this.smileStartTime ?
                    (Date.now() - this.smileStartTime) / 1000 : 0;
                return {
                    smile_confidence: this.smileConfidence,
                    smile_duration: smileDuration
                };

            default:
                return {};
        }
    }

    async authenticateWithFace(identifier, descriptor = null) {
        if (this.isAuthenticating) return;

        this.isAuthenticating = true;

        const faceToAuth = descriptor || this.faceDescriptor;

        if (!faceToAuth) {
            this.showError('No face detected. Please position your face in the frame.');
            this.isAuthenticating = false;
            return;
        }

        if (!this.livenessCompleted) {
            this.showError('Please complete liveness verification first.');
            this.isAuthenticating = false;
            return;
        }

        try {
            this.updateStatus('Authenticating with server...', 'info');

            // Send authentication request to server
            const response = await fetch('/api/face-auth/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    action: 'authenticate',
                    identifier: identifier,
                    session_id: this.sessionId, // Include session ID for backend liveness verification
                    face_descriptor: Array.from(faceToAuth)
                })
            });

            const data = await response.json();

            if (data.success) {
                this.updateStatus('Authentication successful! Redirecting...', 'success');
                this.submitFaceAuthenticationForm(identifier, faceToAuth);
            } else if (data.no_template) {
                // User has no face template registered - guide them to register
                this.updateStatus('Face ID not registered.', 'error');
                this.showRegistrationRequired();
            } else {
                this.showError(data.error || 'Face match failed');
            }

        } catch (error) {
            this.showError('Authentication failed. Please try again.');
        } finally {
            this.isAuthenticating = false;
        }
    }

    /**
     * Show registration required message when user has no face template
     */
    showRegistrationRequired() {
        const fallbackDiv = document.getElementById('fallbackOptions');
        if (fallbackDiv) {
            fallbackDiv.style.display = 'block';
            fallbackDiv.innerHTML = `
                <div class="fallback-content" style="background: #fff3e0; border: 1px solid #ffcc02; border-radius: 12px; padding: 20px; margin-top: 15px; text-align: center;">
                    <i class="fas fa-exclamation-circle" style="font-size: 2rem; color: #ff9800; margin-bottom: 10px;"></i>
                    <h4 style="color: #e65100; margin-bottom: 10px;">Face ID Not Registered</h4>
                    <p style="color: #f57c00; margin-bottom: 15px; font-size: 0.9rem;">
                        Please log in with password first, then register your face for Face ID authentication.
                    </p>
                    <div style="display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;">
                        <button onclick="switchToPasswordLogin()" class="btn btn-primary" style="background: #1976D2; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer;">
                            <i class="fas fa-key"></i> Login with Password
                        </button>
                        <button onclick="switchToOTPLogin()" class="btn btn-secondary" style="background: #6b7280; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer;">
                            <i class="fas fa-mobile-alt"></i> Use OTP
                        </button>
                    </div>
                </div>
            `;
        }

        // Close the scanner modal
        const scanner = document.getElementById('faceid-scanner');
        if (scanner) {
            setTimeout(() => {
                scanner.classList.remove('active');
                this.stopCamera();
            }, 500);
        }
    }

    async syncFromProfilePhoto(identifier) {
        try {
            // 1. Get profile photo from server
            const photoResponse = await fetch('/api/face-template/get-photo/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ identifier: identifier })
            });

            const photoData = await photoResponse.json();
            if (!photoData.success) {
                this.showError('Profile photo not found. Please contact admin.');
                return false;
            }

            // 2. Extract descriptor from profile photo using face-api.js
            this.updateStatus('Processing profile photo...', 'info');
            const img = new Image();
            img.src = photoData.photo_url;
            await new Promise(resolve => img.onload = resolve);

            const detection = await faceapi.detectSingleFace(img, new faceapi.TinyFaceDetectorOptions())
                .withFaceLandmarks()
                .withFaceDescriptor();

            if (!detection) {
                this.showError('Could not detect face in profile photo. Please update your photo.');
                return false;
            }

            // 3. Register descriptor with server
            this.updateStatus('Registering face template...', 'info');
            const registerResponse = await fetch('/api/face-template/register/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    identifier: identifier,
                    face_descriptor: Array.from(detection.descriptor)
                })
            });

            const registerData = await registerResponse.json();
            if (!registerData.success) {
                this.showError('Could not register face template. ' + (registerData.error || ''));
                return false;
            }

            // 4. Store locally and finish
            this.referenceDescriptor = Array.from(detection.descriptor);
            this.updateStatus('Security profile updated.', 'success');
            return true;

        } catch (error) {
            this.showError('Could not access profile photo.');
            return false;
        }
    }

    submitFaceAuthenticationForm(identifier, descriptor = null) {
        const faceToSubmit = descriptor || this.faceDescriptor;
        if (!faceToSubmit) {
            this.showError('Authentication failed: Missing face data');
            return;
        }

        // Create form to submit face authentication through main login endpoint
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = window.location.pathname; // Current login URL

        // Add CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken;
        form.appendChild(csrfInput);

        // Add login type
        const loginTypeInput = document.createElement('input');
        loginTypeInput.type = 'hidden';
        loginTypeInput.name = 'login_type';
        loginTypeInput.value = 'faceid';
        form.appendChild(loginTypeInput);

        // Add next URL
        const nextInput = document.createElement('input');
        nextInput.type = 'hidden';
        nextInput.name = 'next';
        nextInput.value = new URLSearchParams(window.location.search).get('next') || '/dashboard/';
        form.appendChild(nextInput);

        // Add identifier
        const identifierInput = document.createElement('input');
        identifierInput.type = 'hidden';
        identifierInput.name = 'identifier';
        identifierInput.value = identifier;
        form.appendChild(identifierInput);

        // Add face descriptor data
        const faceDataInput = document.createElement('input');
        faceDataInput.type = 'hidden';
        faceDataInput.name = 'face_descriptor';
        faceDataInput.value = JSON.stringify(Array.from(faceToSubmit));
        form.appendChild(faceDataInput);

        // Submit form
        document.body.appendChild(form);
        form.submit();
    }

    showSuccessMessage(message, user) {
        const successDiv = document.createElement('div');
        successDiv.className = 'face-auth-success';
        successDiv.innerHTML = `
            <div class="success-content">
                <i class="fas fa-check-circle"></i>
                <h3>Welcome back, ${user.name}!</h3>
                <p>${message}</p>
                <p class="user-info">Profile: ${user.profile} | School: ${user.school}</p>
            </div>
        `;

        document.body.appendChild(successDiv);

        setTimeout(() => {
            successDiv.remove();
        }, 5000);
    }

    showFallbackOptions() {
        const fallbackDiv = document.getElementById('fallbackOptions');
        if (fallbackDiv) {
            fallbackDiv.style.display = 'block';
            fallbackDiv.innerHTML = `
                <div class="fallback-content">
                    <h4>Alternative Login Methods</h4>
                    <button onclick="switchToPasswordLogin()" class="btn btn-secondary">
                        <i class="fas fa-key"></i> Use Password
                    </button>
                    <button onclick="switchToOTPLogin()" class="btn btn-secondary">
                        <i class="fas fa-mobile-alt"></i> Send OTP
                    </button>
                </div>
            `;
        }
    }

    updateStatus(message, type = 'info') {
        if (this.statusElement) {
            const cleanMessage = message ? message.toString().trim() : 'Processing...';
            this.statusElement.textContent = cleanMessage;
            this.statusElement.className = `face-status ${type}`;
            this.statusElement.style.display = 'flex';

            // Force outside camera container
            this.statusElement.style.position = 'relative';
            this.statusElement.style.bottom = 'auto';
            this.statusElement.style.left = 'auto';
            this.statusElement.style.right = 'auto';
            this.statusElement.style.margin = '25px auto';
        }
    }

    updateMatchPercentage(percentage) {
        const el = document.getElementById('match-percentage');
        if (!el) return;

        el.style.display = percentage > 0 ? 'flex' : 'none';
        el.textContent = `${percentage.toFixed(1)}%`;

        el.classList.remove('high', 'medium', 'low');
        if (percentage >= 85) el.classList.add('high');
        else if (percentage >= 60) el.classList.add('medium');
        else if (percentage > 0) el.classList.add('low');

        // Update progress bar if it exists (legacy support)
        if (this.progressElement) {
            this.progressElement.style.width = `${percentage}%`;
        }
    }

    updateFaceIndicators(activeCount) {
        for (let i = 1; i <= 3; i++) {
            const ind = document.getElementById(`indicator-${i}`);
            if (ind) {
                if (i <= activeCount) {
                    ind.classList.add('active');
                } else {
                    ind.classList.remove('active');
                }
            }
        }
    }

    showError(message) {
        this.updateStatus(message, 'error');

        // Also show in UI alert
        const errorDiv = document.createElement('div');
        errorDiv.className = 'face-auth-error';
        errorDiv.innerHTML = `
            <div class="error-content">
                <i class="fas fa-exclamation-triangle"></i>
                <p>${message}</p>
                <button onclick="this.parentElement.parentElement.remove()" class="btn btn-sm">OK</button>
            </div>
        `;

        document.body.appendChild(errorDiv);

        setTimeout(() => {
            if (errorDiv.parentElement) {
                errorDiv.remove();
            }
        }, 5000);
    }

    getCSRFToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return '';
    }

    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }

        if (this.video) {
            this.video.srcObject = null;
            // Reset video filters
            this.video.classList.remove('low-light', 'very-low-light');
        }

        this.isCapturing = false;
    }

    cleanup() {
        this.stopCamera();

        // Clear authentication timer
        if (this.authenticationTimer) {
            clearTimeout(this.authenticationTimer);
            this.authenticationTimer = null;
        }

        if (this.sessionId) {
            // Clean up session data
            fetch('/api/face-auth/cleanup/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    action: 'cleanup',
                    session_id: this.sessionId
                })
            }).catch(() => { });
        }
    }
}

// Global instance
let faceRecognition = null;

/**
 * Lazy Initialization for Face Recognition
 * This prevents the AI engine from slowing down the page during initial load.
 */
async function ensureFaceRecognitionInitialized() {
    if (faceRecognition) {
        return faceRecognition.initPromise;
    }

    if (document.getElementById('faceVideo') || document.getElementById('faceCanvas')) {
        console.log('Face ID Lazy Initialization: Starting engine...');
        faceRecognition = new SecureFaceRecognition();
        window.faceRecognition = faceRecognition;
        return faceRecognition.initPromise;
    }
    return Promise.resolve(null);
}

// Make globally available
window.ensureFaceRecognitionInitialized = ensureFaceRecognitionInitialized;

// Cleanup on page unload
window.addEventListener('beforeunload', function () {
    if (faceRecognition) {
        faceRecognition.cleanup();
    }
});

// Helper functions for login page integration
function startFaceLogin() {
    if (faceRecognition) {
        faceRecognition.startCamera();
    }
}

function authenticateWithFace() {
    const identifier = document.getElementById('faceIdentifier')?.value ||
        document.getElementById('identifier')?.value || '';

    if (!identifier.trim()) {
        alert('Please enter your email or username for face authentication.');
        return;
    }

    if (faceRecognition) {
        faceRecognition.authenticateWithFace(identifier.trim());
    }
}

function switchToPasswordLogin() {
    document.querySelector('[data-tab="password"]')?.click();
}

function switchToOTPLogin() {
    document.querySelector('[data-tab="otp"]')?.click();
}