<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('transcript_requests', function (Blueprint $table) {
            $table->id();
            $table->foreignId('student_id')->constrained()->cascadeOnDelete();
            $table->enum('status', ['pending', 'approved', 'rejected'])->default('pending');
            $table->string('document_number')->nullable();
            $table->date('document_date')->nullable();
            $table->text('admin_notes')->nullable(); // Catatan dari admin jika ditolak
            $table->string('file_path')->nullable(); // Path ke file PDF transkrip yang sudah jadi
            $table->foreignId('processed_by')->nullable()->constrained('users'); // ID admin yang memproses
            $table->timestamp('processed_at')->nullable();
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('transcript_requests');
    }
};
