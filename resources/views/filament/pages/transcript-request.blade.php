<x-filament-panels::page>
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {{-- Kolom Utama untuk Checklist --}}
        <div class="lg:col-span-2 space-y-6">
            <x-filament::section>
                <x-slot name="heading">
                    <div class="flex items-center gap-2">
                        <x-heroicon-s-clipboard-document-list class="w-6 h-6" />
                        <span>Syarat Permohonan Transkrip</span>
                    </div>
                </x-slot>

                {{-- Gunakan Infolist di sini untuk menampilkan checklist --}}
                {{ $this->requirementsInfolist }}

                {{-- Pesan Status --}}
                {{-- @if(!$latestRequest || $latestRequest->status !== 'approved') --}}
                <div class="mt-6 border-t pt-6">
                    @if ($allRequirementsMet)
                    <div class="flex items-center gap-3 text-sm text-success-600">
                        <x-heroicon-s-check-badge class="w-5 h-5" />
                        <span>Selamat! Semua syarat sudah terpenuhi. Anda dapat mengajukan permohonan melalui tombol di
                            pojok kanan atas.</span>
                    </div>
                    @else
                    <div class="flex items-center gap-3 text-sm text-danger-600">
                        <x-heroicon-s-exclamation-triangle class="w-5 h-5" />
                        <span>Anda belum dapat mengajukan permohonan. Penuhi semua syarat di atas terlebih
                            dahulu.</span>
                    </div>
                    @endif
                </div>
                {{-- @endif --}}
            </x-filament::section>
        </div>

        {{-- Kolom Samping untuk Status Permohonan --}}
        <div class="lg:col-span-1 space-y-6">
            @if($latestRequest)
            @if($latestRequest->status === 'pending')
            <x-filament::section icon="heroicon-s-clock" icon-color="warning">
                <x-slot name="heading">Status: Sedang Diproses</x-slot>
                <p class="text-sm">Permohonan Anda diajukan pada <strong>{{
                        $latestRequest->created_at->translatedFormat('d F Y') }}</strong> dan sedang menunggu
                    persetujuan admin.</p>
            </x-filament::section>
            @elseif($latestRequest->status === 'approved')
            <x-filament::section icon="heroicon-s-check-badge" icon-color="success">
                <x-slot name="heading">Status: Disetujui</x-slot>
                <p class="text-sm mb-4">Permohonan Transkrip Anda telah disetujui pada <strong>{{
                        $latestRequest->processed_at->translatedFormat('d F Y') }}</strong>.</p>
                <x-filament::button tag="a" href="{{ Storage::url($latestRequest->file_path) }}" target="_blank"
                    icon="heroicon-s-arrow-down-tray" class="w-full">
                    Download Transkrip Anda
                </x-filament::button>
            </x-filament::section>
            @elseif($latestRequest->status === 'rejected')
            <x-filament::section icon="heroicon-s-x-circle" icon-color="danger">
                <x-slot name="heading">Status: Ditolak</x-slot>
                <p class="text-sm">Mohon maaf, permohonan Anda ditolak. Silakan hubungi bagian kemahasiswaan untuk
                    informasi lebih lanjut.</p>
                @if($latestRequest->admin_notes)
                <p class="mt-2 text-xs text-gray-500 border-t pt-2"><strong>Catatan Admin:</strong> {{
                    $latestRequest->admin_notes }}</p>
                @endif
            </x-filament::section>
            @endif
            @else
            <x-filament::section icon="heroicon-s-information-circle" icon-color="info">
                <x-slot name="heading">Belum Ada Permohonan</x-slot>
                <p class="text-sm">Anda belum mengajukan permohonan transkrip.</p>
            </x-filament::section>
            @endif
        </div>
    </div>
</x-filament-panels::page>
