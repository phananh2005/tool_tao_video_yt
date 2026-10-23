import re

with open('web/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. HTML Phase 2
p2_start = html.find('<!-- PHASE 2: SCRIPT BUILDER -->')
p3_start = html.find('<!-- PHASE 3: VOICE STUDIO -->')

new_p2 = '''<!-- PHASE 2: SCRIPT BUILDER -->
            <div v-if="currentScreen === 'phase2' && scriptData">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-xl font-bold">📝 Phase 2: Script Builder</h2>
                    <div class="flex items-center gap-4">
                        <span v-if="isScriptDirty" class="text-yellow-600 font-semibold text-sm">⚠️ Có thay đổi chưa lưu</span>
                        <button @click="saveScript" class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded">Lưu Kịch Bản</button>
                        <button @click="generateVoiceover" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded font-bold">Tạo Voiceover ➡️</button>
                    </div>
                </div>
                
                <div class="bg-white p-4 rounded shadow mb-4 flex justify-between items-center">
                    <p class="text-lg"><strong>Thời lượng ước tính:</strong> <span class="text-blue-600 font-bold">{{ scriptData.estimated_total_duration }}s</span></p>
                </div>
                
                <div class="space-y-8">
                    <!-- Group by Chapter -->
                    <div v-for="(group, chapterNum) in groupedScenes" :key="chapterNum" class="border-2 border-gray-200 rounded-lg p-4 bg-gray-50">
                        <h3 class="text-xl font-bold text-gray-800 mb-4 border-b border-gray-300 pb-2">Chapter {{ chapterNum }}</h3>
                        
                        <div class="space-y-4">
                            <div v-for="scene in group" :key="scene.scene_number" class="bg-white p-4 rounded-lg shadow-sm border border-gray-300">
                                <h4 class="font-bold text-gray-700 mb-3 flex justify-between">
                                    <span>🎬 Scene {{ scene.scene_number }}</span>
                                    <span class="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded font-mono">⏱ {{ scene.duration_seconds }}s</span>
                                </h4>
                                <div class="mb-4">
                                    <label class="block text-sm font-semibold text-gray-600 mb-1">Visual Concept (Gợi ý hình ảnh):</label>
                                    <textarea v-model="scene.visual_concept" @input="markScriptDirty" class="w-full border border-gray-300 bg-gray-50 text-gray-700 italic p-2 rounded focus:ring-2 focus:ring-blue-400" rows="2"></textarea>
                                </div>
                                <div>
                                    <label class="block text-sm font-semibold text-gray-600 mb-1">Narration Outline (Lời bình - Tự động tính thời lượng):</label>
                                    <textarea :value="scene.narration_outline.join('\\n')" @input="e => updateNarration(scene, e.target.value)" class="w-full border border-gray-300 p-2 rounded focus:ring-2 focus:ring-blue-400" rows="4"></textarea>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            '''

html = html[:p2_start] + new_p2 + html[p3_start:]

# 2. Add isScriptDirty
html = html.replace("loadingMsg: 'Đang xử lý...'", "loadingMsg: 'Đang xử lý...',\n                    isScriptDirty: false")

# 3. Add computed
computed_str = '''computed: {
                groupedScenes() {
                    if (!this.scriptData || !this.scriptData.scenes) return {};
                    return this.scriptData.scenes.reduce((acc, scene) => {
                        const chapter = scene.chapter_number || '1';
                        if (!acc[chapter]) acc[chapter] = [];
                        acc[chapter].push(scene);
                        return acc;
                    }, {});
                }
            },
            mounted() {'''
html = html.replace("mounted() {", computed_str)

# 4. Add methods
methods_str = '''methods: {
                markScriptDirty() {
                    this.isScriptDirty = true;
                },
                updateNarration(scene, text) {
                    this.markScriptDirty();
                    scene.narration_outline = text.split('\\n').filter(line => line.trim().length > 0);
                    const totalWords = scene.narration_outline.reduce((count, line) => count + line.trim().split(/\\s+/).length, 0);
                    scene.duration_seconds = Math.max(2, Math.round(totalWords / 3.0) + 2);
                    this.recalculateTotalDuration();
                },
                recalculateTotalDuration() {
                    if (!this.scriptData || !this.scriptData.scenes) return;
                    this.scriptData.estimated_total_duration = this.scriptData.scenes.reduce((sum, s) => sum + (s.duration_seconds || 0), 0);
                },'''
html = html.replace("methods: {", methods_str)

# 5. reset isScriptDirty on save and load
html = html.replace('this.scriptData = await this.apiCall("/api/scripts/" + scriptId);', 'this.scriptData = await this.apiCall("/api/scripts/" + scriptId);\n                        this.isScriptDirty = false;')

# For save, we replace the line that calls PUT api/scripts
html = html.replace("await this.apiCall(\"/api/scripts/\" + this.currentProject.current_script_id, 'PUT', { content: this.scriptData });", "await this.apiCall(\"/api/scripts/\" + this.currentProject.current_script_id, 'PUT', { content: this.scriptData });\n                        this.isScriptDirty = false;")

with open('web/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('Success')