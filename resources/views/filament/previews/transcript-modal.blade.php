<div>
    <div class="flex justify-between items-center mb-2">
        <h3 class="text-lg font-semibold">Preview Draf Transkrip</h3>
        <a href="{{ route('transcript.preview', ['transcriptRequest' => $record]) }}" target="_blank"
            class="text-gray-500 hover:text-primary-600">
            <div class="flex justify-between gap-2">
                <span class="text-sm">Buka di tab baru</span>
                <x-heroicon-o-arrow-top-right-on-square class="w-5 h-5" />
            </div>
        </a>
    </div>
    <p class="text-sm text-gray-500 mb-4">
        Ini adalah tampilan draf transkrip yang akan dihasilkan. Silakan isi nomor dan tanggal surat di bawah ini
        sebelum memproses.
    </p>
    <iframe src="{{ route('transcript.preview', ['transcriptRequest' => $record]) }}"
        class="w-full h-[70vh] md:h-[80vh]" loading="lazy" referrerpolicy="no-referrer" scrolling="auto"
        allowfullscreen></iframe>
</div>