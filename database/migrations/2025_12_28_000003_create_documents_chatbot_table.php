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
        Schema::create('documents_chatbot', function (Blueprint $table) {
            $table->id();
            $table->string('filename', 255);
            $table->string('original_name', 255)->nullable();
            $table->foreignId('category_id')->nullable()->constrained('categories_document')->nullOnDelete();
            $table->integer('file_size')->nullable();
            $table->integer('chunk_count')->nullable();
            $table->timestamp('uploaded_at')->nullable();
            $table->timestamp('indexed_at')->nullable();
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('documents_chatbot');
    }
};
